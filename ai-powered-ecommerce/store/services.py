from collections import Counter
from decimal import Decimal
from secrets import token_urlsafe

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from .models import Cart, CartItem, Order, OrderItem, Product, UserInteraction


def session_cart_key(request):
    key = request.session.get("cart_token")
    if not key:
        key = token_urlsafe(24)
        request.session["cart_token"] = key
    return key


def get_cart(request):
    session_key = session_cart_key(request)
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        guest = Cart.objects.filter(session_key=session_key).first()
        if guest and guest.pk != cart.pk:
            for item in guest.items.all():
                row, created = CartItem.objects.get_or_create(cart=cart, product=item.product, defaults={"quantity": item.quantity})
                if not created:
                    row.quantity += item.quantity
                    row.save(update_fields=["quantity"])
            guest.delete()
        return cart
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def record_interaction(request, kind, product=None, category=None, query=""):
    session_key = session_cart_key(request)
    UserInteraction.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key, product=product, category=category,
        kind=kind, query=query[:200],
    )


def create_order_from_cart(user, cart):
    with transaction.atomic():
        items = list(cart.items.select_related("product").select_for_update())
        if not items:
            raise ValueError("Your cart is empty.")
        order = Order.objects.create(user=user)
        total = Decimal("0.00")
        for item in items:
            product = Product.objects.select_for_update().filter(pk=item.product_id, active=True).first()
            if not product:
                raise ValueError(f"{item.product.name} is no longer available.")
            if item.quantity > product.stock_quantity:
                raise ValueError(f"Only {product.stock_quantity} of {product.name} are currently available.")
            line_total = product.price * item.quantity
            OrderItem.objects.create(order=order, product=product, product_name=product.name,
                                     quantity=item.quantity, unit_price=product.price)
            product.stock_quantity -= item.quantity
            product.save(update_fields=["stock_quantity", "updated_at"])
            total += line_total
            record_interaction_for_user(user, product, UserInteraction.Kind.PURCHASE)
        order.total_amount = total
        order.save(update_fields=["total_amount", "updated_at"])
        cart.items.all().delete()
        return order


def record_interaction_for_user(user, product, kind):
    UserInteraction.objects.create(user=user, product=product, category=product.category, kind=kind)


def recommendation_sets(user=None, session_key="", limit=8):
    products = Product.objects.filter(active=True, category__active=True, stock_quantity__gt=0).select_related("category")
    popular_ids = list(UserInteraction.objects.filter(
        kind__in=[UserInteraction.Kind.PURCHASE, UserInteraction.Kind.ADD_TO_CART],
        created_at__gte=timezone.now() - timedelta(days=30), product__active=True,
    ).values("product").annotate(score=Count("id")).order_by("-score", "product")[:limit].values_list("product", flat=True))
    if len(popular_ids) < limit:
        for pk in products.annotate(pop=Count("interactions", filter=Q(interactions__created_at__gte=timezone.now()-timedelta(days=30)))).order_by("-pop", "-created_at").values_list("pk", flat=True):
            if pk not in popular_ids:
                popular_ids.append(pk)
            if len(popular_ids) >= limit:
                break
    trending = list(products.filter(pk__in=popular_ids))
    trending.sort(key=lambda p: popular_ids.index(p.pk))

    interactions = UserInteraction.objects.filter(product__active=True)
    if user and user.is_authenticated:
        interactions = interactions.filter(Q(user=user) | Q(session_key=session_key))
    elif session_key:
        interactions = interactions.filter(session_key=session_key)
    else:
        interactions = interactions.none()
    weights = {"view": 1, "search": 1, "add_to_cart": 3, "purchase": 5, "recommendation_click": 2}
    history = list(interactions.select_related("product", "category").order_by("-created_at")[:300])
    product_scores, category_scores = Counter(), Counter()
    seen_ids = set()
    for event in history:
        weight = weights.get(event.kind, 1)
        if event.product_id:
            product_scores[event.product_id] += weight
            if event.kind in ("purchase", "add_to_cart"):
                seen_ids.add(event.product_id)
            if event.product.category_id:
                category_scores[event.product.category_id] += weight
        if event.category_id:
            category_scores[event.category_id] += weight
        if event.kind == UserInteraction.Kind.SEARCH and event.query:
            matching_categories = Product.objects.filter(active=True, category__active=True).filter(
                Q(name__icontains=event.query) | Q(description__icontains=event.query)
            ).values_list("category_id", flat=True).distinct()[:10]
            for category_id in matching_categories:
                category_scores[category_id] += weight

    personalized = []
    if category_scores:
        candidates = list(products.filter(category_id__in=category_scores).exclude(pk__in=seen_ids))
        candidates.sort(key=lambda p: (category_scores[p.category_id], product_scores.get(p.pk, 0), p.created_at), reverse=True)
        for product in candidates[:limit]:
            product.recommendation_reason = f"Based on your interest in {product.category.name}."
            personalized.append(product)
    if not personalized:
        personalized = list(products.exclude(pk__in=seen_ids).order_by("-created_at")[:limit])
        for product in personalized:
            product.recommendation_reason = "A fresh pick to help you discover the store."

    viewed_categories = {event.product.category_id for event in history if event.product_id and event.kind == "view"}
    similar = []
    if viewed_categories:
        similar = list(products.filter(category_id__in=viewed_categories).exclude(pk__in=seen_ids).order_by("-created_at")[:limit])
        for product in similar:
            product.recommendation_reason = f"Similar items from {product.category.name}."
    return {"personalized": personalized, "trending": trending, "similar": similar}

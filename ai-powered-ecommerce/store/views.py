import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CategoryForm, OrderStatusForm, ProductForm, RegisterForm
from .models import CartItem, Category, Order, Product, UserInteraction
from .services import create_order_from_cart, get_cart, recommendation_sets, record_interaction, session_cart_key


def home(request):
    recs = recommendation_sets(request.user, session_cart_key(request))
    return render(request, "store/home.html", {"recommendations": recs, "categories": Category.objects.filter(active=True)[:6]})


def product_list(request):
    query = request.GET.get("q", "").strip()[:100]
    category_slug = request.GET.get("category", "")
    products = Product.objects.filter(active=True, category__active=True).select_related("category")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))
        record_interaction(request, UserInteraction.Kind.SEARCH, query=query)
    if category_slug:
        products = products.filter(category__slug=category_slug, category__active=True)
        category = Category.objects.filter(slug=category_slug).first()
        if category:
            record_interaction(request, UserInteraction.Kind.SEARCH, category=category, query=query)
    sort = request.GET.get("sort", "newest")
    products = products.order_by("price" if sort == "price" else "-price" if sort == "price_desc" else "name" if sort == "name" else "-created_at")
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(request, "store/product_list.html", {"page_obj": page, "query": query, "selected_category": category_slug, "sort": sort, "categories": Category.objects.filter(active=True)})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, active=True, category__active=True)
    record_interaction(request, UserInteraction.Kind.VIEW, product=product)
    recs = recommendation_sets(request.user, session_cart_key(request))
    similar = list(Product.objects.filter(active=True, stock_quantity__gt=0, category=product.category).exclude(pk=product.pk)[:4])
    for item in similar:
        item.recommendation_reason = f"Similar items from {item.category.name}."
    return render(request, "store/product_detail.html", {"product": product, "similar": similar})


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("home")
    return render(request, "store/auth_form.html", {"form": form, "title": "Create account"})


def cart_detail(request):
    cart = get_cart(request)
    items = cart.items.select_related("product", "product__category")
    total = sum(item.subtotal for item in items)
    return render(request, "store/cart.html", {"cart": cart, "items": items, "total": total})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)
    if product.stock_quantity < 1:
        messages.error(request, "This product is out of stock.")
        return redirect(request.POST.get("next") or "cart")
    cart = get_cart(request)
    row, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": 1})
    if not created:
        row.quantity = min(row.quantity + 1, product.stock_quantity)
        row.save(update_fields=["quantity"])
    record_interaction(request, UserInteraction.Kind.ADD_TO_CART, product=product)
    messages.success(request, f"{product.name} added to your cart.")
    return redirect(request.POST.get("next") or "cart")


@require_POST
def cart_update(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 0
    if quantity <= 0:
        item.delete()
    elif quantity > item.product.stock_quantity:
        messages.error(request, f"Only {item.product.stock_quantity} available.")
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
    return redirect("cart")


@require_POST
def cart_remove(request, item_id):
    get_object_or_404(CartItem, pk=item_id, cart=get_cart(request)).delete()
    messages.info(request, "Item removed from your cart.")
    return redirect("cart")


@login_required
def checkout(request):
    cart = get_cart(request)
    if request.method == "POST":
        try:
            order = create_order_from_cart(request.user, cart)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("cart")
        messages.success(request, "Your order has been placed.")
        return redirect("order_confirmation", order_id=order.pk)
    return render(request, "store/checkout.html", {"items": cart.items.select_related("product"), "total": sum(i.subtotal for i in cart.items.select_related("product"))})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=order_id, user=request.user)
    return render(request, "store/order_detail.html", {"order": order, "confirmation": True})


@login_required
def order_history(request):
    page = Paginator(Order.objects.filter(user=request.user).prefetch_related("items"), 10).get_page(request.GET.get("page"))
    return render(request, "store/orders.html", {"page_obj": page})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=order_id, user=request.user)
    return render(request, "store/order_detail.html", {"order": order})


def recommendations_api(request):
    recs = recommendation_sets(request.user, session_cart_key(request))
    data = {key: [{"id": p.id, "name": p.name, "slug": p.slug, "price": str(p.price), "image_url": p.image_url, "reason": getattr(p, "recommendation_reason", "Popular with shoppers.")} for p in values] for key, values in recs.items()}
    return JsonResponse(data)


@require_POST
def recommendation_click(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)
    record_interaction(request, UserInteraction.Kind.RECOMMENDATION_CLICK, product=product)
    return JsonResponse({"ok": True})


@staff_member_required
def dashboard(request):
    context = {"product_count": Product.objects.count(), "order_count": Order.objects.count(),
               "pending_count": Order.objects.filter(status=Order.Status.PENDING).count(),
               "revenue": Order.objects.exclude(status=Order.Status.CANCELLED).aggregate(total=Sum("total_amount"))["total"] or 0,
               "recent_orders": Order.objects.select_related("user").order_by("-created_at")[:8],
               "top_products": Product.objects.annotate(sales=Sum("order_items__quantity")).order_by("-sales")[:5]}
    return render(request, "store/dashboard.html", context)


@staff_member_required
def admin_products(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product created.")
        return redirect("admin_products")
    return render(request, "store/admin_products.html", {"form": form, "products": Product.objects.select_related("category").order_by("name")})


@staff_member_required
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("admin_products")
    return render(request, "store/admin_form.html", {"form": form, "title": "Edit product"})


@staff_member_required
@require_POST
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.active = False
    product.save(update_fields=["active", "updated_at"])
    messages.info(request, "Product deactivated. Existing order records remain intact.")
    return redirect("admin_products")


@staff_member_required
def admin_categories(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect("admin_categories")
    return render(request, "store/admin_categories.html", {"form": form, "categories": Category.objects.annotate(product_count=Count("products"))})


@staff_member_required
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect("admin_categories")
    return render(request, "store/admin_form.html", {"form": form, "title": "Edit category"})


@staff_member_required
@require_POST
def admin_category_delete(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    category.active = False
    category.save(update_fields=["active"])
    messages.info(request, "Category deactivated. Existing orders and products remain intact.")
    return redirect("admin_categories")


@staff_member_required
def admin_orders(request):
    page = Paginator(Order.objects.select_related("user").prefetch_related("items"), 20).get_page(request.GET.get("page"))
    return render(request, "store/admin_orders.html", {"page_obj": page})


@staff_member_required
def admin_order_edit(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    form = OrderStatusForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Order status updated.")
        return redirect("admin_orders")
    return render(request, "store/admin_form.html", {"form": form, "title": f"Update order #{order.pk}"})

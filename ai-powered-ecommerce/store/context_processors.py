from .models import Category


def store_context(request):
    count = 0
    if request.user.is_authenticated:
        cart = getattr(request.user, "cart", None)
        if cart:
            count = sum(item.quantity for item in cart.items.all())
    elif request.session.get("cart_token"):
        from .models import Cart
        cart = Cart.objects.filter(session_key=request.session.get("cart_token")).first()
        if cart:
            count = sum(item.quantity for item in cart.items.all())
    return {"nav_categories": Category.objects.filter(active=True), "cart_count": count}

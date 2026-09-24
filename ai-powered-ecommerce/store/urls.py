from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"), path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="store/auth_form.html", extra_context={"title": "Sign in"}), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cart/", views.cart_detail, name="cart"), path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/item/<int:item_id>/update/", views.cart_update, name="cart_update"), path("cart/item/<int:item_id>/remove/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"), path("orders/", views.order_history, name="order_history"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"), path("orders/<int:order_id>/confirmation/", views.order_confirmation, name="order_confirmation"),
    path("api/recommendations/", views.recommendations_api, name="recommendations_api"),
    path("api/recommendations/<int:product_id>/click/", views.recommendation_click, name="recommendation_click"),
    path("manage/", views.dashboard, name="dashboard"), path("manage/products/", views.admin_products, name="admin_products"),
    path("manage/products/<int:product_id>/edit/", views.admin_product_edit, name="admin_product_edit"), path("manage/products/<int:product_id>/delete/", views.admin_product_delete, name="admin_product_delete"),
    path("manage/categories/", views.admin_categories, name="admin_categories"), path("manage/categories/<int:category_id>/edit/", views.admin_category_edit, name="admin_category_edit"),
    path("manage/categories/<int:category_id>/delete/", views.admin_category_delete, name="admin_category_delete"),
    path("manage/orders/", views.admin_orders, name="admin_orders"), path("manage/orders/<int:order_id>/", views.admin_order_edit, name="admin_order_edit"),
]

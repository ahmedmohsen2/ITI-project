from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Cart, CartItem, Category, Order, Product, UserInteraction


class CommerceFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Home", description="Objects for the home")
        self.product = Product.objects.create(category=self.category, name="Oak tray", description="A useful tray", price=Decimal("24.50"), stock_quantity=5)
        self.user = User.objects.create_user(username="customer", password="safe-password-123", email="customer@example.com")

    def test_guest_cart_merges_after_login(self):
        self.client.post(reverse("cart_add", args=[self.product.pk]))
        self.assertEqual(CartItem.objects.count(), 1)
        self.client.login(username="customer", password="safe-password-123")
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.get(product=self.product).quantity, 1)
        self.assertFalse(Cart.objects.filter(session_key__isnull=False).exists())

    def test_checkout_uses_server_price_decrements_stock_and_records_purchase(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_login(self.user)
        response = self.client.post(reverse("checkout"))
        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse("order_confirmation", args=[order.pk]))
        self.product.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("49.00"))
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertFalse(cart.items.exists())
        self.assertTrue(UserInteraction.objects.filter(user=self.user, kind=UserInteraction.Kind.PURCHASE).exists())

    def test_checkout_rejects_insufficient_stock_without_partial_order(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=6)
        self.client.force_login(self.user)
        self.client.post(reverse("checkout"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(cart.items.count(), 1)

    def test_customer_cannot_read_another_users_order(self):
        other = User.objects.create_user(username="other", password="safe-password-123")
        order = Order.objects.create(user=other, total_amount=Decimal("0.00"))
        self.client.force_login(self.user)
        response = self.client.get(reverse("order_detail", args=[order.pk]))
        self.assertEqual(response.status_code, 404)

    def test_staff_pages_require_staff_authorization(self):
        response = self.client.get(reverse("admin_products"))
        self.assertEqual(response.status_code, 302)
        staff = User.objects.create_user(username="staff", password="safe-password-123", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("admin_products")).status_code, 200)

    def test_recommendation_api_returns_all_sections_for_a_cold_start(self):
        response = self.client.get(reverse("recommendations_api"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"personalized", "trending", "similar"})
        self.assertTrue(response.json()["personalized"])

    def test_staff_can_deactivate_catalog_items_without_erasing_order_history(self):
        staff = User.objects.create_user(username="staff", password="safe-password-123", is_staff=True)
        order = Order.objects.create(user=self.user, total_amount=Decimal("24.50"))
        order.items.create(product=self.product, product_name=self.product.name, quantity=1, unit_price=self.product.price)
        self.client.force_login(staff)
        self.client.post(reverse("admin_product_delete", args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertFalse(self.product.active)
        self.assertEqual(order.items.count(), 1)

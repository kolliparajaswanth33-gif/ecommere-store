from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Order, Product


User = get_user_model()


class CustomerOrderFlowTests(TestCase):

    def setUp(self):
        self.user = self._create_user("customer")
        self.product = Product.objects.create(
            name="Rice",
            description="A pantry staple",
            price=Decimal("50.00"),
            image_url="https://example.com/rice.jpg",
            stock=5,
        )

    def _create_user(self, username, is_staff=False):
        return User.objects.create_user(
            username=username,
            password="safe-password-123",
            is_staff=is_staff,
        )

    def test_checkout_creates_pending_order_and_returns_home(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        response = self.client.post(
            reverse("store:checkout"),
            {
                "full_name": "Customer Name",
                "email": "customer@example.com",
                "phone": "9876543210",
                "address": "12 Market Road",
                "city": "Vijayawada",
                "postal_code": "520001",
                "payment_method": "upi",
                "utr_number": "UTR123456",
            },
        )

        self.assertRedirects(response, reverse("store:home"))
        order = Order.objects.get()
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.payment_status, "pending")
        self.assertEqual(order.payment_method, "upi")
        self.assertEqual(order.utr_number, "UTR123456")

        response = self.client.get(reverse("store:my_orders"))
        self.assertContains(response, f"Order #{order.id}")

    def test_customer_can_cancel_only_a_pending_order_and_stock_is_restored(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9876543210",
            address="12 Market Road",
            city="Vijayawada",
            postal_code="520001",
            total_amount=Decimal("50.00"),
        )
        order.items.create(
            product=self.product,
            product_name=self.product.name,
            price=self.product.price,
            quantity=2,
        )
        self.product.stock = 3
        self.product.save(update_fields=["stock"])
        self.client.force_login(self.user)

        response = self.client.post(reverse("store:cancel_order", args=[order.id]))

        self.assertRedirects(response, reverse("store:my_orders"))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(self.product.stock, 5)

    def test_customer_cannot_cancel_an_order_after_confirmation(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9876543210",
            address="12 Market Road",
            city="Vijayawada",
            postal_code="520001",
            total_amount=Decimal("50.00"),
            status="confirmed",
        )
        self.client.force_login(self.user)

        self.client.post(reverse("store:cancel_order", args=[order.id]))

        order.refresh_from_db()
        self.assertEqual(order.status, "confirmed")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_HOST_USER="owner@example.com",
    EMAIL_HOST_PASSWORD="test-password",
    DEFAULT_FROM_EMAIL="owner@example.com",
)
class OwnerConfirmationTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="safe-password-123",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username="customer",
            password="safe-password-123",
        )
        self.order = Order.objects.create(
            user=self.customer,
            full_name="Customer Name",
            email="customer@example.com",
            phone="9876543210",
            address="12 Market Road",
            city="Vijayawada",
            postal_code="520001",
            total_amount=Decimal("50.00"),
            payment_method="upi",
            utr_number="UTR123456",
        )

    def test_owner_confirmation_verifies_payment_and_sends_bill(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("management:update_order_status", args=[self.order.id]),
            {"status": "confirmed"},
        )

        self.assertRedirects(response, reverse("management:orders"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "confirmed")
        self.assertEqual(self.order.payment_status, "verified")
        self.assertIsNotNone(self.order.confirmed_at)
        self.assertIsNotNone(self.order.bill_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"Order #{self.order.id}", mail.outbox[0].subject)

    def test_staff_can_only_move_an_order_through_each_delivery_step(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("management:update_order_status", args=[self.order.id]),
            {"status": "delivered"},
        )

        self.assertRedirects(response, reverse("management:orders"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        self.assertEqual(self.order.payment_status, "pending")

        for status in ("confirmed", "packed", "out_for_delivery", "delivered"):
            self.client.post(
                reverse("management:update_order_status", args=[self.order.id]),
                {"status": status},
            )
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, status)

        self.assertEqual(self.order.payment_status, "verified")
        self.assertEqual(len(mail.outbox), 1)

    def test_status_worklists_show_only_orders_in_that_stage(self):
        self.order.status = "packed"
        self.order.payment_status = "verified"
        self.order.save(update_fields=["status", "payment_status"])
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("management:orders_by_status", args=["packed"])
        )

        self.assertContains(response, f"Order #{self.order.id}")
        response = self.client.get(reverse("management:new_orders"))
        self.assertNotContains(response, f"Order #{self.order.id}")

    def test_staff_cancellation_returns_reserved_stock(self):
        product = Product.objects.create(
            name="Sugar",
            description="Pantry item",
            price=Decimal("30.00"),
            image_url="https://example.com/sugar.jpg",
            stock=2,
        )
        self.order.items.create(
            product=product,
            product_name=product.name,
            price=product.price,
            quantity=1,
        )
        product.stock = 1
        product.save(update_fields=["stock"])
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("management:update_order_status", args=[self.order.id]),
            {"status": "cancelled"},
        )

        self.assertRedirects(response, reverse("management:orders"))
        self.order.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")
        self.assertEqual(product.stock, 2)

        response = self.client.get(
            reverse("management:orders_by_status", args=["cancelled"])
        )
        self.assertContains(response, f"Order #{self.order.id}")

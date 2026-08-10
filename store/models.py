from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F


# =========================================================
# PRODUCT
# =========================================================

class Product(models.Model):

    name = models.CharField(
        max_length=200
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    image_url = models.URLField(
        blank=True
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):

        # Customer must choose exactly one:
        # Upload Image OR Image URL

        if bool(self.image) == bool(self.image_url):

            raise ValidationError(
                "Please choose either Upload Image or Image URL."
            )

    class Meta:

        ordering = [
            "-created_at"
        ]

    def __str__(self):

        return self.name


# =========================================================
# ORDER
# =========================================================

class Order(models.Model):

    DELIVERY_TRANSITIONS = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"packed"},
        "packed": {"out_for_delivery"},
        "out_for_delivery": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
    }

    PAYMENT_METHOD_CHOICES = [
        ("upi", "UPI"),
        ("cod", "Cash on Delivery"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending verification"),
        ("verified", "Verified"),
    ]

    STATUS_CHOICES = [

        (
            "pending",
            "Pending"
        ),

        (
            "confirmed",
            "Confirmed"
        ),

        (
            "packed",
            "Packed"
        ),

        (
            "out_for_delivery",
            "Out for Delivery"
        ),

        (
            "delivered",
            "Delivered"
        ),

        (
            "cancelled",
            "Cancelled"
        ),

    ]

    # -----------------------------------------------------
    # CUSTOMER
    # -----------------------------------------------------

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    full_name = models.CharField(
        max_length=150
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=15
    )

    # -----------------------------------------------------
    # DELIVERY ADDRESS
    # -----------------------------------------------------

    address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    postal_code = models.CharField(
        max_length=10
    )

    # -----------------------------------------------------
    # ORDER TOTAL
    # -----------------------------------------------------

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # -----------------------------------------------------
    # PAYMENT
    # -----------------------------------------------------

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        default="",
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )

    utr_number = models.CharField(
        max_length=100,
        blank=True,
    )

    payment_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    bill_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------
    # ORDER STATUS
    # -----------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # -----------------------------------------------------
    # CREATED DATE
    # -----------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

    def __str__(self):

        return (
            f"Order #{self.pk} - "
            f"{self.full_name}"
        )

    def can_transition_to(self, status):
        """Return whether status is the next permitted workflow state."""
        return status in self.DELIVERY_TRANSITIONS.get(self.status, set())

    def next_status(self):
        """Return the next non-cancellation status in the delivery workflow."""
        next_steps = self.DELIVERY_TRANSITIONS.get(self.status, set())
        return next(iter(next_steps - {"cancelled"}), None)

    def cancel(self):
        """Cancel a pending order once and return its reserved stock."""
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)

            if not order.can_transition_to("cancelled"):
                return False

            for item in order.items.all():
                Product.objects.filter(pk=item.product_id).update(
                    stock=F("stock") + item.quantity
                )

            order.status = "cancelled"
            order.save(update_fields=["status"])

        self.status = "cancelled"
        return True


# =========================================================
# ORDER ITEM
# =========================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
    )

    product_name = models.CharField(
        max_length=200
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    quantity = models.PositiveIntegerField()

    def __str__(self):

        return (
            f"{self.quantity} × "
            f"{self.product_name}"
        )


# =========================================================
# COUPON
# =========================================================

class Coupon(models.Model):

    DISCOUNT_TYPES = [

        (
            "flat",
            "Flat Discount"
        ),

        (
            "percentage",
            "Percentage Discount"
        ),

    ]

    code = models.CharField(
        max_length=20,
        unique=True
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES,
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    max_uses = models.PositiveIntegerField(
        default=0
    )

    used_count = models.PositiveIntegerField(
        default=0
    )

    start_date = models.DateField()

    end_date = models.DateField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.code


# =========================================================
# ADDRESS
# =========================================================

class Address(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    full_name = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=15
    )

    house_no = models.CharField(
        max_length=100
    )

    street = models.CharField(
        max_length=200
    )

    landmark = models.CharField(
        max_length=200,
        blank=True
    )

    city = models.CharField(
        max_length=100
    )

    district = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    pincode = models.CharField(
        max_length=6
    )

    is_default = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-is_default",
            "-created_at"
        ]

    def __str__(self):

        return (
            f"{self.full_name} - "
            f"{self.city}"
        )


# =========================================================
# PAYMENT SETTINGS
# =========================================================

class PaymentSettings(models.Model):

    # -----------------------------------------------------
    # UPI ID
    # -----------------------------------------------------

    upi_id = models.CharField(
        max_length=100,
        blank=True
    )

    # -----------------------------------------------------
    # UPI QR CODE
    # -----------------------------------------------------

    qr_code = models.ImageField(
        upload_to="payment/",
        blank=True,
        null=True
    )

    # -----------------------------------------------------
    # PAYMENT OPTIONS
    # -----------------------------------------------------

    upi_enabled = models.BooleanField(
        default=True
    )

    cod_enabled = models.BooleanField(
        default=True
    )

    # -----------------------------------------------------
    # PAYMENT INSTRUCTIONS
    # -----------------------------------------------------

    payment_instructions = models.TextField(
        blank=True,
        default="Pay the exact amount shown above."
    )

    # -----------------------------------------------------
    # LAST UPDATED
    # -----------------------------------------------------

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return "Payment Settings"

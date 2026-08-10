from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from store.emails import send_order_receipt

from store.models import (
    Order,
    Product,
    Coupon,
    PaymentSettings,
)

from .forms import (
    ProductForm,
    CouponForm,
    PaymentSettingsForm,
)


User = get_user_model()


# ============================================================
# MANAGEMENT ACCESS CHECK
# ============================================================

def has_management_access(user):
    return user.is_authenticated and user.is_staff


# ============================================================
# MANAGEMENT LOGIN
# ============================================================

def management_login(request):

    if has_management_access(request.user):
        return redirect("management:dashboard")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not username or not password:

            messages.error(
                request,
                "Please enter username and password."
            )

        else:

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is not None and user.is_staff:

                login(
                    request,
                    user
                )

                return redirect(
                    "management:dashboard"
                )

            messages.error(
                request,
                "Invalid username/password or you do not have management access."
            )

    return render(
        request,
        "management/login.html"
    )


# ============================================================
# MANAGEMENT LOGOUT
# ============================================================

@login_required(login_url="management:login")
def management_logout(request):

    logout(request)

    return redirect(
        "management:login"
    )


# ============================================================
# DASHBOARD
# ============================================================

@login_required(login_url="management:login")
def dashboard(request):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    today = timezone.localdate()

    today_orders = (
        Order.objects
        .filter(created_at__date=today)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    today_orders_count = today_orders.count()

    today_revenue = (
        today_orders.aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    total_products = Product.objects.count()

    total_customers = (
        User.objects
        .filter(is_staff=False)
        .count()
    )

    pending_orders_count = Order.objects.filter(
        status="pending"
    ).count()

    return render(
        request,
        "management/dashboard.html",
        {
            "today_orders": today_orders,
            "today_orders_count": today_orders_count,
            "today_revenue": today_revenue,
            "total_products": total_products,
            "total_customers": total_customers,
            "pending_orders_count": pending_orders_count,
        }
    )


# ============================================================
# PRODUCTS
# ============================================================

@login_required(login_url="management:login")
def products(request):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    all_products = (
        Product.objects
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "management/products.html",
        {
            "products": all_products
        }
    )


# ============================================================
# ADD PRODUCT
# ============================================================

@login_required(login_url="management:login")
def add_product(request):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            product = form.save()

            messages.success(
                request,
                f"{product.name} added successfully."
            )

            return redirect(
                "management:products"
            )

    else:

        form = ProductForm()

    return render(
        request,
        "management/product_form.html",
        {
            "form": form,
            "title": "Add Product"
        }
    )


# ============================================================
# EDIT PRODUCT
# ============================================================

@login_required(login_url="management:login")
def edit_product(request, product_id):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():

            product = form.save()

            messages.success(
                request,
                f"{product.name} updated successfully."
            )

            return redirect(
                "management:products"
            )

    else:

        form = ProductForm(
            instance=product
        )

    return render(
        request,
        "management/product_form.html",
        {
            "form": form,
            "title": "Edit Product",
            "product": product
        }
    )


# ============================================================
# DELETE PRODUCT
# ============================================================

@login_required(login_url="management:login")
def delete_product(request, product_id):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product_name = product.name

        product.delete()

        messages.success(
            request,
            f"{product_name} deleted successfully."
        )

    return redirect(
        "management:products"
    )


# ============================================================
# ALL ORDERS
# ============================================================

@login_required(login_url="management:login")
def orders(request):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    all_orders = (
        Order.objects
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "management/orders.html",
        {
            "orders": all_orders,
            "page_title": "All Orders",
            "page_description": (
                "View and manage all customer orders placed in "
                "Kubera Kirana Shop."
            ),
            "return_to": "orders",
        }
    )


# ============================================================
# NEW ORDERS (PENDING ONLY)
# ============================================================

@login_required(login_url="management:login")
def new_orders(request):

    if not request.user.is_staff:
        messages.error(request, "You do not have management access.")
        return redirect("management:login")

    pending_orders = (
        Order.objects
        .filter(status="pending")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "management/orders.html",
        {
            "orders": pending_orders,
            "page_title": "New Orders",
            "page_description": (
                "Review pending customer orders. Confirmed or cancelled "
                "orders are removed from this list automatically."
            ),
            "return_to": "new_orders",
            "is_new_orders_page": True,
        }
    )


# ============================================================
# DELIVERY WORKLISTS
# ============================================================

DELIVERY_WORKLISTS = {
    "confirmed": ("Confirmed Orders", "Orders awaiting packing."),
    "packed": ("Packed Orders", "Orders ready to be sent for delivery."),
    "out_for_delivery": ("Out for Delivery", "Orders currently with delivery staff."),
    "delivered": ("Delivered Orders", "Completed customer deliveries."),
    "cancelled": ("Cancelled Orders", "Orders cancelled by the customer or staff."),
}


@login_required(login_url="management:login")
def orders_by_status(request, status):

    if not request.user.is_staff:
        messages.error(request, "You do not have management access.")
        return redirect("management:login")

    if status not in DELIVERY_WORKLISTS:
        messages.error(request, "That order worklist is not available.")
        return redirect("management:orders")

    page_title, page_description = DELIVERY_WORKLISTS[status]
    status_orders = (
        Order.objects.filter(status=status)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "management/orders.html",
        {
            "orders": status_orders,
            "page_title": page_title,
            "page_description": page_description,
            "return_to": status,
        },
    )


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@login_required(login_url="management:login")
def update_order_status(request, order_id):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    order = get_object_or_404(
        Order,
        id=order_id
    )

    return_to = request.POST.get("return_to", "orders")

    def return_to_worklist():
        if return_to == "new_orders":
            return redirect("management:new_orders")
        if return_to in DELIVERY_WORKLISTS:
            return redirect("management:orders_by_status", status=return_to)
        return redirect("management:orders")

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request."
        )

        return return_to_worklist()

    status = request.POST.get(
        "status",
        ""
    ).strip().lower()

    allowed_statuses = {
        value
        for value, label in Order.STATUS_CHOICES
    }

    if status not in allowed_statuses:

        messages.error(
            request,
            "Invalid order status."
        )

        return return_to_worklist()

    if not order.can_transition_to(status):
        messages.error(
            request,
            (
                f"Order #{order.id} cannot move from "
                f"{order.get_status_display()} directly to "
                f"{dict(Order.STATUS_CHOICES).get(status, status)}."
            ),
        )
        return return_to_worklist()

    if status == "cancelled":
        if order.cancel():
            messages.success(
                request,
                f"Order #{order.id} was cancelled and its stock was returned.",
            )
        else:
            messages.error(
                request,
                f"Order #{order.id} can no longer be cancelled.",
            )
        return return_to_worklist()

    now = timezone.now()
    was_pending = order.status == "pending"
    update_fields = ["status"]

    order.status = status

    if status == "confirmed" and was_pending:
        order.payment_status = "verified"
        order.payment_verified_at = now
        order.confirmed_at = now
        update_fields.extend(
            [
                "payment_status",
                "payment_verified_at",
                "confirmed_at",
            ]
        )

    order.save(update_fields=update_fields)

    if status == "confirmed" and was_pending:
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            try:
                send_order_receipt(order)
            except Exception:
                messages.warning(
                    request,
                    (
                        "Order was confirmed, but the bill email could not "
                        "be sent. Check the email settings and confirm again "
                        "to retry."
                    ),
                )
            else:
                order.bill_sent_at = timezone.now()
                order.save(update_fields=["bill_sent_at"])
                messages.success(
                    request,
                    f"Order #{order.id} confirmed and bill emailed to the customer.",
                )
                return return_to_worklist()
        else:
            messages.warning(
                request,
                (
                    "Order was confirmed, but no bill email was sent because "
                    "email settings are not configured."
                ),
            )

    messages.success(
        request,
        f"Order #{order.id} status updated to {order.get_status_display()}."
    )

    return return_to_worklist()


# ============================================================
# COUPONS
# ============================================================

@login_required(login_url="management:login")
def coupons(request):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    all_coupons = (
        Coupon.objects
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "management/coupons.html",
        {
            "coupons": all_coupons
        }
    )


# ============================================================
# ADD COUPON
# ============================================================

@login_required(login_url="management:login")
def add_coupon(request):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    if request.method == "POST":

        form = CouponForm(
            request.POST
        )

        if form.is_valid():

            coupon = form.save()

            messages.success(
                request,
                f"Coupon '{coupon.code}' created successfully."
            )

            return redirect(
                "management:coupons"
            )

    else:

        form = CouponForm()

    return render(
        request,
        "management/coupon_form.html",
        {
            "form": form,
            "title": "Add Coupon",
        }
    )


# ============================================================
# EDIT COUPON
# ============================================================

@login_required(login_url="management:login")
def edit_coupon(request, coupon_id):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    coupon = get_object_or_404(
        Coupon,
        id=coupon_id
    )

    if request.method == "POST":

        form = CouponForm(
            request.POST,
            instance=coupon
        )

        if form.is_valid():

            coupon = form.save()

            messages.success(
                request,
                f"Coupon '{coupon.code}' updated successfully."
            )

            return redirect(
                "management:coupons"
            )

    else:

        form = CouponForm(
            instance=coupon
        )

    return render(
        request,
        "management/coupon_form.html",
        {
            "form": form,
            "title": "Edit Coupon",
            "coupon": coupon,
        }
    )


# ============================================================
# DELETE COUPON
# ============================================================

@login_required(login_url="management:login")
def delete_coupon(request, coupon_id):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    coupon = get_object_or_404(
        Coupon,
        id=coupon_id
    )

    if request.method == "POST":

        coupon_code = coupon.code

        coupon.delete()

        messages.success(
            request,
            f"Coupon '{coupon_code}' deleted successfully."
        )

    return redirect(
        "management:coupons"
    )


# ============================================================
# PAYMENT SETTINGS
# ============================================================

@login_required(login_url="management:login")
def payment_settings(request):

    if not has_management_access(request.user):

        messages.error(
            request,
            "You do not have management access."
        )

        return redirect(
            "management:login"
        )

    # Get the existing settings.
    # If there is no record yet, create one.
    payment_settings, created = (
        PaymentSettings.objects.get_or_create(
            id=1
        )
    )

    if request.method == "POST":

        form = PaymentSettingsForm(
            request.POST,
            request.FILES,
            instance=payment_settings
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Payment settings updated successfully."
            )

            return redirect(
                "management:payment_settings"
            )

    else:

        form = PaymentSettingsForm(
            instance=payment_settings
        )

    return render(
        request,
        "management/payment_settings.html",
        {
            "form": form,
            "payment_settings": payment_settings,
        }
    )

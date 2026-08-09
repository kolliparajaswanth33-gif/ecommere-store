from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from store.models import Order, Product, Coupon

from .forms import ProductForm, CouponForm


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

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

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

                login(request, user)

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

    return render(
        request,
        "management/dashboard.html",
        {
            "today_orders": today_orders,
            "today_orders_count": today_orders_count,
            "today_revenue": today_revenue,
            "total_products": total_products,
            "total_customers": total_customers,
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
            "orders": all_orders
        }
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

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request."
        )

        return redirect(
            "management:orders"
        )

    status = request.POST.get(
        "status",
        ""
    ).strip()

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Packed",
        "Shipped",
        "Delivered",
        "Cancelled",
    ]

    if status not in allowed_statuses:

        messages.error(
            request,
            "Invalid order status."
        )

        return redirect(
            "management:orders"
        )

    # IMPORTANT:
    # This requires Order model to have a "status" field.
    order.status = status

    order.save(
        update_fields=["status"]
    )

    messages.success(
        request,
        f"Order #{order.id} status updated to {status}."
    )

    return redirect(
        "management:orders"
    )


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

        code = request.POST.get(
            "code",
            ""
        ).strip().upper()

        discount_type = request.POST.get(
            "discount_type",
            ""
        ).strip()

        discount_value = request.POST.get(
            "discount_value",
            ""
        ).strip()

        minimum_order_amount = request.POST.get(
            "minimum_order_amount",
            "0"
        ).strip()

        max_uses = request.POST.get(
            "max_uses",
            "0"
        ).strip()

        start_date = request.POST.get(
            "start_date",
            ""
        ).strip()

        end_date = request.POST.get(
            "end_date",
            ""
        ).strip()

        is_active = request.POST.get(
            "is_active"
        ) == "on"

        if not code:

            messages.error(
                request,
                "Coupon code is required."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        if Coupon.objects.filter(
            code__iexact=code
        ).exists():

            messages.error(
                request,
                "This coupon code already exists."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        try:

            discount_value = float(
                discount_value
            )

            minimum_order_amount = float(
                minimum_order_amount or 0
            )

            max_uses = int(
                max_uses or 0
            )

        except ValueError:

            messages.error(
                request,
                "Please enter valid coupon values."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        if discount_value <= 0:

            messages.error(
                request,
                "Discount value must be greater than 0."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        if discount_type not in [
            "flat",
            "percentage"
        ]:

            messages.error(
                request,
                "Invalid discount type."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        if (
            discount_type == "percentage"
            and discount_value > 100
        ):

            messages.error(
                request,
                "Percentage discount cannot be greater than 100."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        if not start_date or not end_date:

            messages.error(
                request,
                "Please select start and end dates."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        if end_date < start_date:

            messages.error(
                request,
                "End date cannot be before start date."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Add Coupon"
                }
            )

        Coupon.objects.create(

            code=code,

            discount_type=discount_type,

            discount_value=discount_value,

            minimum_order_amount=minimum_order_amount,

            max_uses=max_uses,

            start_date=start_date,

            end_date=end_date,

            is_active=is_active
        )

        messages.success(
            request,
            f"Coupon {code} created successfully."
        )

        return redirect(
            "management:coupons"
        )

    return render(
        request,
        "management/coupon_form.html",
        {
            "title": "Add Coupon"
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

        code = request.POST.get(
            "code",
            ""
        ).strip().upper()

        discount_type = request.POST.get(
            "discount_type",
            ""
        ).strip()

        discount_value = request.POST.get(
            "discount_value",
            ""
        ).strip()

        minimum_order_amount = request.POST.get(
            "minimum_order_amount",
            "0"
        ).strip()

        max_uses = request.POST.get(
            "max_uses",
            "0"
        ).strip()

        start_date = request.POST.get(
            "start_date",
            ""
        ).strip()

        end_date = request.POST.get(
            "end_date",
            ""
        ).strip()

        is_active = request.POST.get(
            "is_active"
        ) == "on"

        if not code:

            messages.error(
                request,
                "Coupon code is required."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        duplicate = (
            Coupon.objects
            .filter(code__iexact=code)
            .exclude(id=coupon.id)
            .exists()
        )

        if duplicate:

            messages.error(
                request,
                "Another coupon already uses this code."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        try:

            discount_value = float(
                discount_value
            )

            minimum_order_amount = float(
                minimum_order_amount or 0
            )

            max_uses = int(
                max_uses or 0
            )

        except ValueError:

            messages.error(
                request,
                "Please enter valid coupon values."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        if discount_value <= 0:

            messages.error(
                request,
                "Discount value must be greater than 0."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        if discount_type not in [
            "flat",
            "percentage"
        ]:

            messages.error(
                request,
                "Invalid discount type."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        if (
            discount_type == "percentage"
            and discount_value > 100
        ):

            messages.error(
                request,
                "Percentage discount cannot be greater than 100."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        if not start_date or not end_date:

            messages.error(
                request,
                "Please select start and end dates."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        if end_date < start_date:

            messages.error(
                request,
                "End date cannot be before start date."
            )

            return render(
                request,
                "management/coupon_form.html",
                {
                    "title": "Edit Coupon",
                    "coupon": coupon
                }
            )

        coupon.code = code

        coupon.discount_type = discount_type

        coupon.discount_value = discount_value

        coupon.minimum_order_amount = (
            minimum_order_amount
        )

        coupon.max_uses = max_uses

        coupon.start_date = start_date

        coupon.end_date = end_date

        coupon.is_active = is_active

        coupon.save()

        messages.success(
            request,
            f"Coupon {code} updated successfully."
        )

        return redirect(
            "management:coupons"
        )

    return render(
        request,
        "management/coupon_form.html",
        {
            "title": "Edit Coupon",
            "coupon": coupon
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
            f"Coupon {coupon_code} deleted successfully."
        )

    return redirect(
        "management:coupons"
    )

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

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

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
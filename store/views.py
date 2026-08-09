from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .cart import cart_total, get_cart
from .emails import send_order_receipt
from .forms import RegisterForm
from .models import Address, Coupon, Order, OrderItem, Product


# ============================================================
# HOME
# ============================================================

@login_required(login_url="store:login")
def home(request):

    products = Product.objects.all().order_by("-created_at")

    return render(
        request,
        "store/home.html",
        {
            "products": products,
        }
    )


# ============================================================
# PRODUCT DETAIL
# ============================================================

def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
        }
    )


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(
                request,
                user
            )

            return redirect(
                "store:home"
            )

    else:

        form = RegisterForm()

    return render(
        request,
        "store/register.html",
        {
            "form": form,
        }
    )


# ============================================================
# CART ITEMS HELPER
# ============================================================

def _cart_items(request):

    cart = get_cart(
        request.session
    )

    products = Product.objects.filter(
        id__in=cart.keys()
    )

    items = []

    for product in products:

        quantity = cart.get(
            str(product.id),
            0
        )

        if quantity > 0:

            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "subtotal": product.price * quantity,
                }
            )

    return items


# ============================================================
# ADD TO CART
# ============================================================

def add_to_cart(request, product_id):

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Use the add-to-cart button."
        )

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if product.stock <= 0:

        messages.error(
            request,
            f"{product.name} is out of stock."
        )

        return redirect(
            "store:product_detail",
            product_id=product.id
        )

    cart = get_cart(
        request.session
    )

    product_id = str(
        product.id
    )

    current_quantity = cart.get(
        product_id,
        0
    )

    cart[product_id] = min(
        current_quantity + 1,
        product.stock
    )

    request.session["cart"] = cart
    request.session.modified = True

    return redirect(
        "store:cart"
    )


# ============================================================
# BUY NOW
# ============================================================

def buy_now(request, product_id):

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Use the buy-now button."
        )

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if product.stock <= 0:

        messages.error(
            request,
            "This product is out of stock."
        )

        return redirect(
            "store:product_detail",
            product_id=product.id
        )

    # Clear existing cart.
    # Buy Now should contain ONLY this product.

    cart = {}

    cart[str(product.id)] = 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect(
        "store:checkout"
    )


# ============================================================
# CART
# ============================================================

def cart_view(request):

    items = _cart_items(
        request
    )

    total = cart_total(
        items
    )

    return render(
        request,
        "store/cart.html",
        {
            "items": items,
            "total": total,
        }
    )


# ============================================================
# UPDATE CART
# ============================================================

def update_cart(request, product_id):

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Use the cart form."
        )

    product = get_object_or_404(
        Product,
        id=product_id
    )

    cart = get_cart(
        request.session
    )

    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1
            )
        )

    except (TypeError, ValueError):

        quantity = 1

    if quantity <= 0:

        cart.pop(
            str(product.id),
            None
        )

    else:

        if product.stock <= 0:

            cart.pop(
                str(product.id),
                None
            )

            messages.error(
                request,
                f"{product.name} is out of stock."
            )

        else:

            cart[str(product.id)] = min(
                quantity,
                product.stock
            )

    request.session["cart"] = cart
    request.session.modified = True

    return redirect(
        "store:cart"
    )


# ============================================================
# CHECKOUT
# ============================================================

@login_required(login_url="store:login")
def checkout(request):

    items = _cart_items(
        request
    )

    total = cart_total(
        items
    )

    discount = 0
    final_total = total
    coupon = None

    # ========================================================
    # EMPTY CART
    # ========================================================

    if not items:

        messages.warning(
            request,
            "Your cart is empty."
        )

        return redirect(
            "store:home"
        )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        # ====================================================
        # COUPON CODE
        # ====================================================

        coupon_code = request.POST.get(
            "coupon_code",
            ""
        ).strip().upper()

        if coupon_code:

            try:

                coupon = Coupon.objects.get(
                    code__iexact=coupon_code
                )

                today = timezone.localdate()

                # =================================================
                # CHECK 1 - ACTIVE
                # =================================================

                if not coupon.is_active:

                    messages.warning(
                        request,
                        "This coupon is inactive. "
                        "Your order will continue without a discount."
                    )

                    coupon = None

                # =================================================
                # CHECK 2 - START DATE
                # =================================================

                elif today < coupon.start_date:

                    messages.warning(
                        request,
                        "This coupon is not active yet. "
                        "Your order will continue without a discount."
                    )

                    coupon = None

                # =================================================
                # CHECK 3 - END DATE
                # =================================================

                elif today > coupon.end_date:

                    messages.warning(
                        request,
                        "This coupon has expired. "
                        "Your order will continue without a discount."
                    )

                    coupon = None

                # =================================================
                # CHECK 4 - MAXIMUM USES
                # =================================================

                elif (
                    coupon.max_uses > 0
                    and coupon.used_count >= coupon.max_uses
                ):

                    messages.warning(
                        request,
                        "This coupon has reached its usage limit. "
                        "Your order will continue without a discount."
                    )

                    coupon = None

                # =================================================
                # CHECK 5 - MINIMUM ORDER
                # =================================================

                elif (
                    total < coupon.minimum_order_amount
                ):

                    messages.warning(
                        request,
                        f"This coupon requires a minimum order "
                        f"of ₹{coupon.minimum_order_amount}. "
                        "Your order will continue without a discount."
                    )

                    coupon = None

                # =================================================
                # CHECK 6 - DISCOUNT TYPE
                # =================================================

                else:

                    if coupon.discount_type == "flat":

                        discount = coupon.discount_value

                    elif coupon.discount_type == "percentage":

                        discount = (
                            total
                            * coupon.discount_value
                            / 100
                        )

                    else:

                        discount = 0

                    # Discount can never be greater
                    # than the order total.

                    discount = min(
                        discount,
                        total
                    )

                    messages.success(
                        request,
                        f"Coupon '{coupon.code}' "
                        f"applied successfully!"
                    )

            except Coupon.DoesNotExist:

                # IMPORTANT:
                # Invalid coupon NEVER blocks the order.

                messages.warning(
                    request,
                    "Invalid coupon code. "
                    "Your order will continue without a discount."
                )

                coupon = None

        # ====================================================
        # FINAL TOTAL
        # ====================================================

        final_total = max(
            total - discount,
            0
        )

        # ====================================================
        # CUSTOMER DETAILS
        # ====================================================

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        city = request.POST.get(
            "city",
            ""
        ).strip()

        postal_code = request.POST.get(
            "postal_code",
            ""
        ).strip()

        # ====================================================
        # BASIC VALIDATION
        # ====================================================

        if not full_name:

            messages.error(
                request,
                "Please enter your full name."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "discount": discount,
                    "final_total": final_total,
                    "coupon": coupon,
                    "user": request.user,
                }
            )

        if not email:

            messages.error(
                request,
                "Please enter your email."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "discount": discount,
                    "final_total": final_total,
                    "coupon": coupon,
                    "user": request.user,
                }
            )

        if not phone:

            messages.error(
                request,
                "Please enter your phone number."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "discount": discount,
                    "final_total": final_total,
                    "coupon": coupon,
                    "user": request.user,
                }
            )

        if not address:

            messages.error(
                request,
                "Please enter your address."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "discount": discount,
                    "final_total": final_total,
                    "coupon": coupon,
                    "user": request.user,
                }
            )

        if not city:

            messages.error(
                request,
                "Please enter your city."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "discount": discount,
                    "final_total": final_total,
                    "coupon": coupon,
                    "user": request.user,
                }
            )

        if not postal_code:

            messages.error(
                request,
                "Please enter your postal code."
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "discount": discount,
                    "final_total": final_total,
                    "coupon": coupon,
                    "user": request.user,
                }
            )

        # ====================================================
        # CREATE ORDER
        # ====================================================

        try:

            with transaction.atomic():

                order = Order.objects.create(

                    user=request.user,

                    full_name=full_name,

                    email=email,

                    phone=phone,

                    address=address,

                    city=city,

                    postal_code=postal_code,

                    total_amount=final_total,

                )

                # =================================================
                # SAVE CUSTOMER ADDRESS
                # =================================================

                Address.objects.update_or_create(

                    user=request.user,

                    is_default=True,

                    defaults={

                        "full_name": full_name,

                        "phone": phone,

                        "house_no": address,

                        "street": "",

                        "landmark": "",

                        "city": city,

                        "district": city,

                        "state": "Andhra Pradesh",

                        "pincode": postal_code,

                    },

                )

                # =================================================
                # SAVE ORDER ITEMS
                # =================================================

                for item in items:

                    product = item["product"]

                    quantity = item["quantity"]

                    # ---------------------------------------------
                    # STOCK SAFETY
                    # ---------------------------------------------

                    if product.stock < quantity:

                        raise ValueError(
                            f"Not enough stock for {product.name}."
                        )

                    # ---------------------------------------------
                    # CREATE ORDER ITEM
                    # ---------------------------------------------

                    OrderItem.objects.create(

                        order=order,

                        product=product,

                        product_name=product.name,

                        price=product.price,

                        quantity=quantity,

                    )

                    # ---------------------------------------------
                    # REDUCE STOCK
                    # ---------------------------------------------

                    product.stock -= quantity

                    product.save(
                        update_fields=[
                            "stock"
                        ]
                    )

                # =================================================
                # COUPON USAGE
                # =================================================

                # Increase usage ONLY when coupon was valid
                # and actually applied.

                if coupon:

                    coupon.used_count += 1

                    coupon.save(
                        update_fields=[
                            "used_count"
                        ]
                    )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "store/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "discount": discount,
                    "final_total": final_total,
                    "coupon": coupon,
                    "user": request.user,
                }
            )

        # ====================================================
        # CLEAR CART
        # ====================================================

        request.session["cart"] = {}

        request.session.modified = True

        # ====================================================
        # SEND EMAIL
        # ====================================================

        if (
            settings.EMAIL_HOST_USER
            and settings.EMAIL_HOST_PASSWORD
        ):

            transaction.on_commit(
                lambda: send_order_receipt(order)
            )

        # ====================================================
        # ORDER SUCCESS
        # ====================================================

        return redirect(
            "store:order_success",
            order_id=order.id
        )

    # ========================================================
    # GET REQUEST
    # ========================================================

    return render(
        request,
        "store/checkout.html",
        {
            "items": items,
            "total": total,
            "discount": discount,
            "final_total": final_total,
            "coupon": coupon,
            "user": request.user,
        }
    )


# ============================================================
# ORDER SUCCESS
# ============================================================

@login_required(login_url="store:login")
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "store/order_success.html",
        {
            "order": order,
        }
    )


# ============================================================
# CUSTOMER DASHBOARD
# ============================================================

@login_required(login_url="store:login")
def dashboard(request):

    today = timezone.localdate()

    today_orders = (
        Order.objects
        .filter(
            created_at__date=today
        )
        .prefetch_related(
            "items"
        )
        .order_by(
            "-created_at"
        )
    )

    today_orders_count = today_orders.count()

    today_revenue = (
        today_orders
        .aggregate(
            total=Sum(
                "total_amount"
            )
        )["total"]
        or 0
    )

    total_products = Product.objects.count()

    total_customers = User.objects.count()

    context = {

        "today_orders_count":
            today_orders_count,

        "today_revenue":
            today_revenue,

        "total_products":
            total_products,

        "total_customers":
            total_customers,

        "today_orders":
            today_orders,

    }

    return render(
        request,
        "store/dashboard/dashboard.html",
        context
    )


# ============================================================
# MANAGEMENT LOGIN
# ============================================================

def management_login(request):

    if (
        request.user.is_authenticated
        and request.user.is_staff
    ):

        return redirect(
            "management:dashboard"
        )

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if (
            user is not None
            and user.is_staff
        ):

            login(
                request,
                user
            )

            return redirect(
                "management:dashboard"
            )

        messages.error(
            request,
            "Invalid management username or password."
        )

    return render(
        request,
        "store/management/login.html"
    )


# ============================================================
# MANAGEMENT LOGOUT
# ============================================================

def management_logout(request):

    logout(
        request
    )

    return redirect(
        "management:login"
    )
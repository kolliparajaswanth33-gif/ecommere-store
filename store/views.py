from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .cart import cart_total, get_cart
from .forms import RegisterForm, AddressForm
from .models import (
    Address,
    Coupon,
    Order,
    OrderItem,
    Product,
    PaymentSettings,
)


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
        },
    )


# ============================================================
# PRODUCT DETAIL
# ============================================================

def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
        },
    )


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.user.is_authenticated:
        return redirect("store:home")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Registration successful. Welcome!",
            )

            return redirect("store:home")

    else:

        form = RegisterForm()

    return render(
        request,
        "store/register.html",
        {
            "form": form,
        },
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("store:home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                "Login successful.",
            )

            return redirect("store:home")

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "store/login.html",
    )


# ============================================================
# LOGOUT
# ============================================================

@login_required(login_url="store:login")
def logout_view(request):

    if request.method == "POST":

        logout(request)

        messages.success(
            request,
            "You have been logged out successfully.",
        )

        return redirect("store:login")

    return redirect("store:home")


# ============================================================
# CART ITEMS HELPER
# ============================================================

def _cart_items(request):

    cart = get_cart(request.session)

    if not cart:
        return []

    products = Product.objects.filter(
        id__in=cart.keys()
    )

    items = []

    for product in products:

        quantity = cart.get(
            str(product.id),
            0,
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
            "Use the Add to Cart button."
        )

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    if product.stock <= 0:

        messages.error(
            request,
            f"{product.name} is out of stock.",
        )

        return redirect(
            "store:product_detail",
            product_id=product.id,
        )

    cart = get_cart(request.session)

    product_key = str(product.id)

    current_quantity = cart.get(
        product_key,
        0,
    )

    if current_quantity >= product.stock:

        messages.warning(
            request,
            f"Only {product.stock} units of "
            f"{product.name} are available.",
        )

    else:

        cart[product_key] = current_quantity + 1

        request.session["cart"] = cart
        request.session.modified = True

        messages.success(
            request,
            f"{product.name} added to cart.",
        )

    return redirect("store:cart")


# ============================================================
# BUY NOW
# ============================================================

def buy_now(request, product_id):

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Use the Buy Now button."
        )

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    if product.stock <= 0:

        messages.error(
            request,
            "This product is out of stock.",
        )

        return redirect(
            "store:product_detail",
            product_id=product.id,
        )

    request.session["cart"] = {
        str(product.id): 1,
    }

    request.session.modified = True

    return redirect("store:checkout")


# ============================================================
# CART
# ============================================================

def cart_view(request):

    items = _cart_items(request)

    total = cart_total(items)

    return render(
        request,
        "store/cart.html",
        {
            "items": items,
            "total": total,
        },
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
        id=product_id,
    )

    cart = get_cart(request.session)

    product_key = str(product.id)

    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1,
            )
        )

    except (TypeError, ValueError):

        quantity = 1

    if quantity <= 0:

        cart.pop(
            product_key,
            None,
        )

    elif product.stock <= 0:

        cart.pop(
            product_key,
            None,
        )

        messages.error(
            request,
            f"{product.name} is out of stock.",
        )

    else:

        if quantity > product.stock:

            quantity = product.stock

            messages.warning(
                request,
                f"Only {product.stock} units "
                f"are available.",
            )

        cart[product_key] = quantity

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("store:cart")


# ============================================================
# PAYMENT SETTINGS
# ============================================================

def get_payment_settings():

    payment_settings = (
        PaymentSettings.objects
        .filter(id=1)
        .first()
    )

    if payment_settings is None:

        payment_settings = PaymentSettings.objects.create(
            id=1
        )

    return payment_settings


# ============================================================
# COUPON CALCULATION
# ============================================================

def calculate_coupon_discount(
    coupon_code,
    total,
):

    discount = 0
    coupon = None
    message = None

    if not coupon_code:

        return coupon, discount, message

    try:

        coupon = Coupon.objects.get(
            code__iexact=coupon_code
        )

    except Coupon.DoesNotExist:

        return (
            None,
            0,
            "Invalid coupon code.",
        )

    today = timezone.localdate()

    if not coupon.is_active:

        return (
            None,
            0,
            "This coupon is inactive.",
        )

    if today < coupon.start_date:

        return (
            None,
            0,
            "This coupon is not active yet.",
        )

    if today > coupon.end_date:

        return (
            None,
            0,
            "This coupon has expired.",
        )

    if (
        coupon.max_uses > 0
        and coupon.used_count >= coupon.max_uses
    ):

        return (
            None,
            0,
            "This coupon has reached its usage limit.",
        )

    if total < coupon.minimum_order_amount:

        return (
            None,
            0,
            (
                f"This coupon requires a minimum "
                f"order of ₹{coupon.minimum_order_amount}."
            ),
        )

    if coupon.discount_type == "flat":

        discount = coupon.discount_value

    elif coupon.discount_type == "percentage":

        discount = (
            total
            * coupon.discount_value
            / 100
        )

    discount = min(
        discount,
        total,
    )

    return (
        coupon,
        discount,
        None,
    )


# ============================================================
# SAVED ADDRESSES
# ============================================================

@login_required(login_url="store:login")
def addresses(request):

    user_addresses = (
        Address.objects
        .filter(user=request.user)
        .order_by(
            "-is_default",
            "-created_at",
        )
    )

    return render(
        request,
        "store/addresses.html",
        {
            "addresses": user_addresses,
        },
    )


# ============================================================
# ADD NEW ADDRESS
# ============================================================

@login_required(login_url="store:login")
def add_address(request):

    if request.method == "POST":

        form = AddressForm(request.POST)

        if form.is_valid():

            address = form.save(
                commit=False
            )

            address.user = request.user

            # First address automatically becomes default.
            if not Address.objects.filter(
                user=request.user
            ).exists():

                address.is_default = True

            address.save()

            messages.success(
                request,
                "Address added successfully.",
            )

            return redirect(
                "store:addresses"
            )

    else:

        form = AddressForm()

    return render(
        request,
        "store/address_form.html",
        {
            "form": form,
            "title": "Add New Address",
        },
    )


# ============================================================
# EDIT ADDRESS
# ============================================================

@login_required(login_url="store:login")
def edit_address(
    request,
    address_id,
):

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user,
    )

    if request.method == "POST":

        form = AddressForm(
            request.POST,
            instance=address,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Address updated successfully.",
            )

            return redirect(
                "store:addresses"
            )

    else:

        form = AddressForm(
            instance=address
        )

    return render(
        request,
        "store/address_form.html",
        {
            "form": form,
            "title": "Edit Address",
            "address": address,
        },
    )


# ============================================================
# DELETE ADDRESS
# ============================================================

@login_required(login_url="store:login")
def delete_address(
    request,
    address_id,
):

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user,
    )

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Use the Delete button."
        )

    was_default = address.is_default

    address.delete()

    # If default address was deleted,
    # automatically select another address.
    if was_default:

        new_default = (
            Address.objects
            .filter(user=request.user)
            .order_by("-created_at")
            .first()
        )

        if new_default:

            new_default.is_default = True

            new_default.save(
                update_fields=[
                    "is_default"
                ]
            )

    messages.success(
        request,
        "Address deleted successfully.",
    )

    return redirect(
        "store:addresses"
    )


# ============================================================
# SET DEFAULT ADDRESS
# ============================================================

@login_required(login_url="store:login")
def set_default_address(
    request,
    address_id,
):

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Use the Set Default button."
        )

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user,
    )

    # Remove default from every address.
    Address.objects.filter(
        user=request.user
    ).update(
        is_default=False
    )

    # Set selected address as default.
    address.is_default = True

    address.save(
        update_fields=[
            "is_default"
        ]
    )

    messages.success(
        request,
        "Default address changed successfully.",
    )

    return redirect(
        "store:addresses"
    )


# ============================================================
# CHECKOUT
# ============================================================

@login_required(login_url="store:login")
def checkout(request):

    items = _cart_items(request)

    total = cart_total(items)

    discount = 0
    final_total = total
    coupon = None

    payment_settings = get_payment_settings()

    # --------------------------------------------------------
    # EMPTY CART
    # --------------------------------------------------------

    if not items:

        messages.warning(
            request,
            "Your cart is empty.",
        )

        return redirect(
            "store:home"
        )

    # --------------------------------------------------------
    # DEFAULT SAVED ADDRESS
    # --------------------------------------------------------

    default_address = (
        Address.objects
        .filter(
            user=request.user,
            is_default=True,
        )
        .first()
    )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        # ====================================================
        # ADDRESS SELECTION
        # ====================================================

        selected_address_id = request.POST.get(
            "address_id",
            "",
        ).strip()

        selected_address = None

        if selected_address_id:

            try:

                selected_address = Address.objects.get(
                    id=selected_address_id,
                    user=request.user,
                )

            except (
                Address.DoesNotExist,
                ValueError,
            ):

                selected_address = None

        # ====================================================
        # COUPON
        # ====================================================

        coupon_code = request.POST.get(
            "coupon_code",
            "",
        ).strip().upper()

        if coupon_code:

            (
                coupon,
                discount,
                coupon_error,
            ) = calculate_coupon_discount(
                coupon_code,
                total,
            )

            if coupon_error:

                messages.warning(
                    request,
                    coupon_error,
                )

                coupon = None
                discount = 0

            else:

                messages.success(
                    request,
                    f"Coupon '{coupon.code}' "
                    f"applied successfully!",
                )

        # ====================================================
        # TOTAL
        # ====================================================

        final_total = max(
            total - discount,
            0,
        )

        # ====================================================
        # CUSTOMER DETAILS
        # ====================================================

        if selected_address:

            full_name = selected_address.full_name
            phone = selected_address.phone

            address = selected_address.house_no

            if selected_address.street:

                address += (
                    ", "
                    + selected_address.street
                )

            if selected_address.landmark:

                address += (
                    ", "
                    + selected_address.landmark
                )

            city = selected_address.city

            postal_code = selected_address.pincode

        else:

            full_name = request.POST.get(
                "full_name",
                "",
            ).strip()

            phone = request.POST.get(
                "phone",
                "",
            ).strip()

            address = request.POST.get(
                "address",
                "",
            ).strip()

            city = request.POST.get(
                "city",
                "",
            ).strip()

            postal_code = request.POST.get(
                "postal_code",
                "",
            ).strip()

        email = request.POST.get(
            "email",
            "",
        ).strip()

        # ====================================================
        # PAYMENT
        # ====================================================

        payment_method = request.POST.get(
            "payment_method",
            "",
        ).strip().lower()

        utr_number = request.POST.get(
            "utr_number",
            "",
        ).strip()

        # ====================================================
        # VALIDATION
        # ====================================================

        error = None

        if not full_name:

            error = (
                "Please select or enter your name."
            )

        elif not email:

            error = (
                "Please enter your email."
            )

        elif not phone:

            error = (
                "Please select or enter your phone number."
            )

        elif not address:

            error = (
                "Please select or enter your address."
            )

        elif not city:

            error = (
                "Please select or enter your village/town."
            )

        elif not postal_code:

            error = (
                "Please enter your PIN code."
            )

        elif payment_method not in (
            "upi",
            "cod",
        ):

            error = (
                "Please select a valid payment method."
            )

        elif (
            payment_method == "upi"
            and not payment_settings.upi_enabled
        ):

            error = (
                "UPI payment is currently unavailable."
            )

        elif (
            payment_method == "cod"
            and not payment_settings.cod_enabled
        ):

            error = (
                "Cash on Delivery is currently unavailable."
            )

        elif (
            payment_method == "upi"
            and not utr_number
        ):

            error = (
                "Please enter the UTR number "
                "after making the UPI payment."
            )

        # ====================================================
        # SHOW ERROR
        # ====================================================

        if error:

            messages.error(
                request,
                error,
            )

        # ====================================================
        # CREATE ORDER
        # ====================================================

        else:

            try:

                with transaction.atomic():

                    # ----------------------------------------
                    # PAYMENT STATUS
                    # ----------------------------------------

                    payment_status = "pending"

                    # ----------------------------------------
                    # CREATE ORDER
                    # ----------------------------------------

                    order = Order.objects.create(

                        user=request.user,

                        full_name=full_name,

                        email=email,

                        phone=phone,

                        address=address,

                        city=city,

                        postal_code=postal_code,

                        total_amount=final_total,

                        payment_method=payment_method,

                        payment_status=payment_status,

                        utr_number=(
                            utr_number
                            if payment_method == "upi"
                            else ""
                        ),

                        status="pending",
                    )

                    # ----------------------------------------
                    # SAVE ADDRESS
                    # ----------------------------------------

                    if selected_address:

                        # The selected address already exists.
                        pass

                    else:

                        # Save manually entered address
                        # as the user's default address.

                        Address.objects.filter(
                            user=request.user
                        ).update(
                            is_default=False
                        )

                        Address.objects.create(

                            user=request.user,

                            full_name=full_name,

                            phone=phone,

                            house_no=address,

                            street="",

                            landmark="",

                            city=city,

                            district=city,

                            state="Andhra Pradesh",

                            pincode=postal_code,

                            is_default=True,
                        )

                    # ----------------------------------------
                    # ORDER ITEMS
                    # ----------------------------------------

                    for item in items:

                        product = item["product"]

                        quantity = item["quantity"]

                        if product.stock < quantity:

                            raise ValueError(
                                f"Not enough stock for "
                                f"{product.name}."
                            )

                        OrderItem.objects.create(

                            order=order,

                            product=product,

                            product_name=product.name,

                            price=product.price,

                            quantity=quantity,
                        )

                        product.stock -= quantity

                        product.save(
                            update_fields=[
                                "stock"
                            ]
                        )

                    # ----------------------------------------
                    # COUPON
                    # ----------------------------------------

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
                    str(error),
                )

            else:

                # --------------------------------------------
                # CLEAR CART
                # --------------------------------------------

                request.session["cart"] = {}

                request.session.modified = True

                messages.success(
                    request,
                    (
                        f"Order #{order.id} has been placed and is "
                        "pending payment verification."
                    ),
                )

                return redirect("store:home")

    # ========================================================
    # CHECKOUT PAGE
    # ========================================================

    saved_addresses = (
        Address.objects
        .filter(user=request.user)
        .order_by(
            "-is_default",
            "-created_at",
        )
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

            "payment_settings":
                payment_settings,

            "upi_enabled":
                payment_settings.upi_enabled,

            "cod_enabled":
                payment_settings.cod_enabled,

            "upi_id":
                payment_settings.upi_id,

            "qr_code":
                payment_settings.qr_code,

            "payment_instructions":
                payment_settings.payment_instructions,

            # Saved address information
            "addresses":
                saved_addresses,

            "saved_addresses":
                saved_addresses,

            "default_address":
                default_address,
        },
    )


# ============================================================
# ORDER SUCCESS
# ============================================================

@login_required(login_url="store:login")
def order_success(
    request,
    order_id,
):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    messages.info(
        request,
        f"Order #{order.id} is available in My Orders.",
    )

    return redirect("store:my_orders")


# ============================================================
# CUSTOMER ORDERS
# ============================================================

@login_required(login_url="store:login")
def my_orders(request):

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "store/my_orders.html",
        {"orders": orders},
    )


@login_required(login_url="store:login")
def order_detail(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user,
    )

    return render(
        request,
        "store/order_detail.html",
        {"order": order},
    )


@login_required(login_url="store:login")
def cancel_order(request, order_id):
    """Allow a customer to cancel only their own pending order."""
    if request.method != "POST":
        return redirect("store:my_orders")

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user,
    )

    if order.cancel():
        messages.success(
            request,
            f"Order #{order.id} has been cancelled. Any payment refund, if needed, will be handled by the shop.",
        )
    else:
        messages.error(
            request,
            f"Order #{order.id} can no longer be cancelled because it is {order.get_status_display()}.",
        )

    return redirect("store:my_orders")


# ============================================================
# CUSTOMER DASHBOARD
# ============================================================

@login_required(login_url="store:login")
def dashboard(request):

    today = timezone.localdate()

    today_orders = (
        Order.objects
        .filter(
            user=request.user,
            created_at__date=today,
        )
        .prefetch_related("items")
        .order_by("-created_at")
    )

    today_orders_count = today_orders.count()

    today_revenue = (
        today_orders
        .aggregate(
            total=Sum("total_amount")
        )
        ["total"]
        or 0
    )

    total_products = Product.objects.count()

    total_customers = User.objects.count()

    return render(
        request,
        "store/dashboard/dashboard.html",
        {
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
        },
    )

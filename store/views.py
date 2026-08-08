from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .cart import cart_total, get_cart
from .emails import send_order_receipt
from .forms import RegisterForm
from .models import Address, Coupon, Order, OrderItem, Product
@login_required(login_url='store:login')
def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('store:home')
    else:
        form = RegisterForm()

    return render(request, 'store/register.html', {'form': form})


def _cart_items(request):
    cart = get_cart(request.session)
    products = Product.objects.filter(id__in=cart.keys())
    items = []

    for product in products:
        quantity = cart.get(str(product.id), 0)
        if quantity:
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity,
            })
    return items


def add_to_cart(request, product_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Use the add-to-cart button.')

    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request.session)
    product_id = str(product.id)
    cart[product_id] = min(cart.get(product_id, 0) + 1, product.stock)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('store:cart')


def buy_now(request, product_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Use the buy-now button.')

    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request.session)
    cart[str(product.id)] = min(cart.get(str(product.id), 0) + 1, product.stock)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('store:checkout')


def cart_view(request):
    items = _cart_items(request)
    return render(request, 'store/cart.html', {
        'items': items,
        'total': cart_total(items),
    })


def update_cart(request, product_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Use the cart form.')

    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request.session)
    quantity = int(request.POST.get('quantity', 1))
    if quantity <= 0:
        cart.pop(str(product.id), None)
    else:
        cart[str(product.id)] = min(quantity, product.stock)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('store:cart')


@login_required
def checkout(request):
    items = _cart_items(request)
    total = cart_total(items)

    discount = 0
    final_total = total
    coupon = None

    if not items:
        return redirect("store:home")

    if request.method == "POST":

        coupon_code = request.POST.get("coupon_code", "").strip().upper()

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)

                today = timezone.now().date()

                if not coupon.is_active:
                    messages.error(request, "This coupon is inactive.")
                    coupon = None

                elif not (coupon.start_date <= today <= coupon.end_date):
                    messages.error(request, "This coupon has expired.")
                    coupon = None

                elif coupon.max_uses > 0 and coupon.used_count >= coupon.max_uses:
                    messages.error(request, "Coupon usage limit reached.")
                    coupon = None

                elif total < coupon.minimum_order_amount:
                    messages.error(
                        request,
                        f"Minimum order amount is ₹{coupon.minimum_order_amount}"
                    )
                    coupon = None

                else:
                    if coupon.discount_type == "flat":
                        discount = coupon.discount_value
                    else:
                        discount = (total * coupon.discount_value) / 100

                    messages.success(
                        request,
                        f"Coupon '{coupon.code}' applied successfully!"
                    )

            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")

        final_total = max(total - discount, 0)

        with transaction.atomic():

            order = Order.objects.create(
                user=request.user,
                full_name=request.POST["full_name"],
                email=request.POST["email"],
                phone=request.POST["phone"],
                address=request.POST["address"],
                city=request.POST["city"],
                postal_code=request.POST["postal_code"],
                total_amount=final_total,
            )

            # Save customer address
            Address.objects.update_or_create(
                user=request.user,
                is_default=True,
                defaults={
                    "full_name": request.POST["full_name"],
                    "phone": request.POST["phone"],
                    "house_no": request.POST["address"],
                    "street": "",
                    "landmark": "",
                    "city": request.POST["city"],
                    "district": request.POST["city"],
                    "state": "Andhra Pradesh",
                    "pincode": request.POST["postal_code"],
                },
            )

            # Save order items
            for item in items:
                product = item["product"]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    price=product.price,
                    quantity=item["quantity"],
                )

                product.stock -= item["quantity"]
                product.save(update_fields=["stock"])

            # Update coupon usage
            if coupon:
                coupon.used_count += 1
                coupon.save(update_fields=["used_count"])

        request.session["cart"] = {}

        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            transaction.on_commit(lambda: send_order_receipt(order))

        return redirect("store:order_success", order_id=order.id)

    return render(
        request,
        "store/checkout.html",
        {
            "items": items,
            "total": total,
            "discount": discount,
            "final_total": final_total,
            "user": request.user,
        },
    )

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = User.objects.count()

    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
    }

    return render(request, 'store/dashboard/dashboard.html', context)
# Create your views here.

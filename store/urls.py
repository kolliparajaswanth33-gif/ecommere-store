from django.urls import path
from . import views

app_name = "store"

urlpatterns = [

    # =========================================================
    # HOME / PRODUCTS
    # =========================================================

    path("", views.home, name="home"),

    path(
        "product/<int:product_id>/",
        views.product_detail,
        name="product_detail"
    ),


    # =========================================================
    # AUTHENTICATION
    # =========================================================

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),


# =========================================================
# CART
# =========================================================

path(
    "cart/",
    views.cart_view,
    name="cart"
),

path(
    "cart/add/<int:product_id>/",
    views.add_to_cart,
    name="add_to_cart"
),

path(
    "cart/update/<int:product_id>/",
    views.update_cart,
    name="update_cart"
),

    # =========================================================
    # BUY NOW
    # =========================================================

    path(
        "buy-now/<int:product_id>/",
        views.buy_now,
        name="buy_now"
    ),


    # =========================================================
    # CHECKOUT
    # =========================================================

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),


    # =========================================================
    # ORDERS
    # =========================================================

    path(
        "order-success/<int:order_id>/",
        views.order_success,
        name="order_success"
    ),

    path(
        "my-orders/",
        views.my_orders,
        name="my_orders"
    ),

    path(
        "my-orders/<int:order_id>/",
        views.order_detail,
        name="order_detail"
    ),

    path(
        "my-orders/<int:order_id>/cancel/",
        views.cancel_order,
        name="cancel_order"
    ),


    # =========================================================
    # ADDRESSES
    # =========================================================

    path(
        "addresses/",
        views.addresses,
        name="addresses"
    ),

    path(
        "addresses/add/",
        views.add_address,
        name="address_add"
    ),

    path(
        "addresses/<int:address_id>/edit/",
        views.edit_address,
        name="address_edit"
    ),

    path(
        "addresses/<int:address_id>/delete/",
        views.delete_address,
        name="address_delete"
    ),

    path(
        "addresses/<int:address_id>/default/",
        views.set_default_address,
        name="address_default"
    ),

]

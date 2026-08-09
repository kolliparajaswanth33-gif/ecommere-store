from django.urls import path

from . import views


app_name = "management"


urlpatterns = [

    # ============================
    # DASHBOARD
    # ============================

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    # ============================
    # LOGIN
    # ============================

    path(
        "login/",
        views.management_login,
        name="login"
    ),

    # ============================
    # LOGOUT
    # ============================

    path(
        "logout/",
        views.management_logout,
        name="logout"
    ),

    # ============================
    # PRODUCTS
    # ============================

    path(
        "products/",
        views.products,
        name="products"
    ),

    path(
        "products/add/",
        views.add_product,
        name="add_product"
    ),

    path(
        "products/edit/<int:product_id>/",
        views.edit_product,
        name="edit_product"
    ),

    path(
        "products/delete/<int:product_id>/",
        views.delete_product,
        name="delete_product"
    ),

    # ============================
    # ORDERS
    # ============================

    path(
        "orders/",
        views.orders,
        name="orders"
    ),


    path(
    "orders/<int:order_id>/status/",
    views.update_order_status,
    name="update_order_status"
),

# ============================
# COUPONS
# ============================

path(
    "coupons/",
    views.coupons,
    name="coupons"
),

path(
    "coupons/add/",
    views.add_coupon,
    name="add_coupon"
),

path(
    "coupons/edit/<int:coupon_id>/",
    views.edit_coupon,
    name="edit_coupon"
),

path(
    "coupons/delete/<int:coupon_id>/",
    views.delete_coupon,
    name="delete_coupon"
),
]
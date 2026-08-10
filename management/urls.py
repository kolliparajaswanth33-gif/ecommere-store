from django.urls import path

from . import views


app_name = "management"


urlpatterns = [

    # ========================================================
    # LOGIN / LOGOUT
    # ========================================================

    path(
        "login/",
        views.management_login,
        name="login"
    ),

    path(
        "logout/",
        views.management_logout,
        name="logout"
    ),

    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    # ========================================================
    # PRODUCTS
    # ========================================================

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
        "products/<int:product_id>/edit/",
        views.edit_product,
        name="edit_product"
    ),

    path(
        "products/<int:product_id>/delete/",
        views.delete_product,
        name="delete_product"
    ),

    # ========================================================
    # ORDERS
    # ========================================================

    path(
        "orders/",
        views.orders,
        name="orders"
    ),

    path(
        "new-orders/",
        views.new_orders,
        name="new_orders"
    ),

    path(
        "orders/status/<str:status>/",
        views.orders_by_status,
        name="orders_by_status"
    ),

    path(
        "orders/<int:order_id>/status/",
        views.update_order_status,
        name="update_order_status"
    ),

    # ========================================================
    # COUPONS
    # ========================================================

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
        "coupons/<int:coupon_id>/edit/",
        views.edit_coupon,
        name="edit_coupon"
    ),

    path(
        "coupons/<int:coupon_id>/delete/",
        views.delete_coupon,
        name="delete_coupon"
    ),

    # ========================================================
    # PAYMENT SETTINGS
    # ========================================================

    path(
        "payment-settings/",
        views.payment_settings,
        name="payment_settings"
    ),
]

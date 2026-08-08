from django.contrib import admin

from .models import Address, Coupon, Order, OrderItem, Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'created_at')
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'total_amount', 'created_at')
    search_fields = ('full_name', 'phone', 'email')
    readonly_fields = ('total_amount', 'created_at')
    inlines = [OrderItemInline]



@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'discount_type',
        'discount_value',
        'minimum_order_amount',
        'max_uses',
        'used_count',
        'start_date',
        'end_date',
        'is_active',
    )

    search_fields = ('code',)

    list_filter = (
        'is_active',
        'discount_type',
        'start_date',
        'end_date',
    )    

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "user",
        "phone",
        "city",
        "district",
        "state",
        "pincode",
        "is_default",
    )

    list_filter = (
        "state",
        "district",
        "is_default",
    )

    search_fields = (
        "full_name",
        "phone",
        "city",
        "pincode",
    )
# Register your models here.

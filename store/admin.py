from django.contrib import admin

from .models import Order, OrderItem, Product, Address

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

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "user",
        "phone",
        "city",
        "state",
        "pincode",
        "is_default",
    )

    list_filter = (
        "state",
        "city",
        "is_default",
    )

    search_fields = (
        "full_name",
        "phone",
        "city",
        "pincode",
    )
# Register your models here.

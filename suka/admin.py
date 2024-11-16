from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'image_preview')
    list_filter = ('category',)
    search_fields = ('name',)
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image Preview"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'total')

    class OrderItemInline(admin.TabularInline):
        model = OrderItem
        extra = 0

    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('product__name',)

from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Category, Product, Profile, StoreSettings, Order, OrderItem, Cart, CartItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'store_name', 'owner', 'category', 'price', 'stock', 'is_available', 'created_at']
    list_filter = ['owner__store_settings__store_name', 'category', 'is_available', 'created_at']
    list_select_related = ['owner', 'owner__store_settings', 'category']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'owner__username', 'owner__store_settings__store_name']
    list_editable = ['owner', 'price', 'stock', 'is_available']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Store Assignment', {
            'fields': ('owner',)
        }),
        ('Product Information', {
            'fields': ('name', 'slug', 'category', 'description', 'image')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock', 'is_available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Store', ordering='owner__store_settings__store_name')
    def store_name(self, obj):
        if not obj.owner_id:
            return '-'

        store_settings = getattr(obj.owner, 'store_settings', None)
        if store_settings:
            return store_settings.store_name

        return obj.owner.username

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'owner':
            kwargs['queryset'] = User.objects.filter(
                profile__user_type='store_owner'
            ).order_by('store_settings__store_name', 'username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone', 'city', 'created_at']
    list_filter = ['user_type', 'city']
    search_fields = ['user__username', 'phone', 'city']
    readonly_fields = ['created_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type')
        }),
        ('Contact Details', {
            'fields': ('phone', 'address', 'city', 'postal_code')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'owner', 'opening_hours', 'updated_at']
    search_fields = ['store_name', 'owner__username', 'location']
    readonly_fields = ['updated_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'total']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__username', 'email', 'phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'delivered_at']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'total_amount', 'status', 'payment_status')
        }),
        ('Customer Details', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'postal_code')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_confirmed', 'mark_as_delivered', 'mark_as_cancelled']

    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_as_confirmed.short_description = "Mark selected orders as confirmed"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered', delivered_at=timezone.now())
    mark_as_delivered.short_description = "Mark selected orders as delivered"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total', 'get_item_count', 'created_at', 'updated_at']
    search_fields = ['user__username']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'get_total']
    list_filter = ['cart']

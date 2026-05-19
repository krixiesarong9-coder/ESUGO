from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('stores/', views.store_list, name='store_list'),
    path('product/<slug:category_slug>/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),

    path('checkout/', views.checkout, name='checkout'),

    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='order_history'),

    path('pay/<str:order_number>/', views.pay_order, name='pay_order'),
    path('payment-result/<str:order_number>/', views.payment_result, name='payment_result'),

    path('profile/', views.profile_view, name='profile'),

    path('manager/', views.manager_dashboard, name='manager_dashboard'),

    path('store-owner-dashboard/', views.store_owner_dashboard, name='store_owner_dashboard'),
    path('store-owner-dashboard/orders/<str:order_number>/update/', views.store_owner_update_order, name='store_owner_update_order'),
    path('store-owner-dashboard/products/<int:product_id>/delete/', views.store_owner_delete_product, name='store_owner_delete_product'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/stock-alerts/', views.admin_stock_alerts, name='admin_stock_alerts'),
    path('admin-dashboard/stock-alerts/low/', views.admin_low_stock_products, name='admin_low_stock_products'),
    path('admin-dashboard/stock-alerts/out-of-stock/', views.admin_out_of_stock_products, name='admin_out_of_stock_products'),

    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),

    path('rider-dashboard/', views.rider_dashboard, name='rider_dashboard'),
    path('rider/update-status/<str:order_number>/', views.rider_update_status, name='rider_update_status'),

    path('dashboard/assign-rider/<str:order_number>/', views.admin_assign_rider, name='admin_assign_rider'),

    path('accounts/register/', views.register_view, name='register'),
]

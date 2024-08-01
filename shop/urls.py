from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from app import settings
from . import views

urlpatterns = [
    path('', views.home, name='home'),  

    path('buyer/orders/', views.buyer_orders, name='buyer_orders'),
    path('buyer/account-settings/', views.buyer_account_settings, name='buyer_account_settings'),

    path('admn/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('shopowner/dashboard/', views.shopowner_dashboard, name='shopowner_dashboard'),
    path('buyer/dashboard/', views.buyer_dashboard, name='buyer_dashboard'),

    path('dashboard/', views.user_dashboard, name='user_dashboard'),


    path('shopowner/dashboard/', views.shopowner_dashboard, name='shopowner_dashboard'),
    path('shopowner/register/', views.register_shop, name='shopowner_register_shop'),
    path('shopowner/add-product/', views.add_product, name='shopowner_add_product'),
    path('shopowner/orders/', views.view_orders, name='shopowner_orders'),
    path('shopowner/sales-reports/', views.sales_reports, name='shopowner_sales_reports'),

    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('products/', views.product_list, name='product_list'),
    path('contact/', views.contact_view, name='contact'),

    path('manage-users/', views.manage_users, name='manage_users'),
    path('admn/products/', views.manage_products, name='admin_products'),
    path('manage-and-add-categories/', views.manage_and_add_categories, name='manage_and_add_categories'),


    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('mpesa_callback/', views.mpesa_callback, name='mpesa_callback'),
    path('payment/waiting/', views.payment_waiting_page, name='payment_waiting_page'),
    path('payment/status/', views.check_payment_status, name='check_payment_status'),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('sslcommerz/payment/', views.sslcommerz_payment, name='sslcommerz_payment'),
    path('sslcommerz/success/', views.sslcommerz_payment_success, name='sslcommerz_success'),
    path('sslcommerz/fail/', views.sslcommerz_payment_fail, name='sslcommerz_payment_fail'),
    path('sslcommerz/cancel/', views.sslcommerz_payment_cancel, name='sslcommerz_payment_cancel'),
]
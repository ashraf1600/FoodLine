from django.urls import path, include
from . import views
from accounts import views as Account_views




urlpatterns = [
    path('',Account_views.vendorDashboard, name='vendor'),

    path('profile/', views.vprofile, name='vprofile'),
    
]

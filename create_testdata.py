#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodOnline_main.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from vendor.models import Vendor
from menu.models import Category, FoodItem

User = get_user_model()

# Create superuser/admin
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    admin.role = 1  # Admin role
    admin.save()
    print("✓ Admin user created: username=admin, password=admin123")

# Create a vendor account
if not User.objects.filter(username='vendor1').exists():
    vendor_user = User.objects.create_user(
        username='vendor1',
        email='vendor1@test.com',
        password='vendor123',
        first_name='John',
        last_name='Vendor'
    )
    vendor_user.role = 1  # Vendor role
    vendor_user.save()
    
    # Create vendor user profile
    vendor_profile = UserProfile.objects.create(user=vendor_user)
    
    # Create vendor
    vendor = Vendor.objects.create(
        user=vendor_user,
        user_profile=vendor_profile,
        vendor_name='Test Restaurant',
        vendor_slug='test-restaurant',
        vendor_license='vendor/license/default.jpg',
        is_approved=True
    )
    print(f"✓ Vendor account created: username=vendor1, password=vendor123, vendor={vendor.vendor_name}")

# Create a customer account
if not User.objects.filter(username='customer1').exists():
    customer_user = User.objects.create_user(
        username='customer1',
        email='customer1@test.com',
        password='customer123',
        first_name='Jane',
        last_name='Customer'
    )
    customer_user.role = 2  # Customer role
    customer_user.save()
    
    # Create customer profile
    profile = UserProfile.objects.create(
        user=customer_user,
        address='123 Main St',
        city='Test City'
    )
    print(f"✓ Customer account created: username=customer1, password=customer123")

# Create test food items
vendor = Vendor.objects.first()
if vendor:
    category, created = Category.objects.get_or_create(
        vendor=vendor,
        category_name='Burgers',
        defaults={'slug': 'burgers'}
    )
    
    FoodItem.objects.get_or_create(
        vendor=vendor,
        category=category,
        food_title='Deluxe Burger',
        defaults={
            'slug': 'deluxe-burger',
            'description': 'Tasty beef burger with fresh vegetables',
            'price': 8.99,
            'image': 'burger.jpg',
            'is_available': True
        }
    )
    
    FoodItem.objects.get_or_create(
        vendor=vendor,
        category=category,
        food_title='Chicken Burger',
        defaults={
            'slug': 'chicken-burger',
            'description': 'Crispy fried chicken burger',
            'price': 7.99,
            'image': 'chicken_burger.jpg',
            'is_available': True
        }
    )
    
    print(f"✓ Test food items created in {vendor.vendor_name}")

print("\n✅ Test data setup complete!")
print("\nLogin credentials:")
print("  Admin:    username=admin, password=admin123")
print("  Vendor:   username=vendor1, password=vendor123")
print("  Customer: username=customer1, password=customer123")

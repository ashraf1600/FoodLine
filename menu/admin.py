from django.contrib import admin
from .models import Category, FoodItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug', 'vendor', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('category_name',)}
    search_fields = ('category_name', 'vendor__vendor_name')


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('food_title', 'category', 'vendor', 'price', 'is_available', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('food_title',)}
    search_fields = ('food_title', 'category__category_name', 'vendor__vendor_name')
    list_filter = ('is_available', 'category')

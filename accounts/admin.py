from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'role', 'is_active')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ('role', 'is_active', 'is_staff', 'is_admin')

    # Make non-editable fields read-only
    readonly_fields = ('date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('email', 'username', 'first_name', 'last_name', 'password', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superadmin')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'role',
                'is_active',
                'is_staff',
            ),
        }),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)

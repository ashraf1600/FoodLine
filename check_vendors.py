import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodOnline_main.settings')
django.setup()

from vendor.models import Vendor

vendors = Vendor.objects.all()
print(f'Total vendors: {vendors.count()}')
for v in vendors:
    print(f'Vendor: {v.vendor_name}, Slug: "{v.vendor_slug}", Approved: {v.is_approved}')

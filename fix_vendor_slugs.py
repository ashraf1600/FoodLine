import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodOnline_main.settings')
django.setup()

from vendor.models import Vendor

vendors = Vendor.objects.all()
for v in vendors:
    if not v.vendor_slug:
        v.vendor_slug = slugify(v.vendor_name)
        v.save()
        print(f'Updated vendor: {v.vendor_name} -> slug: {v.vendor_slug}')
    else:
        print(f'Vendor {v.vendor_name} already has slug: {v.vendor_slug}')

print('Done!')

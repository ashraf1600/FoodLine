from django import forms
from .models import Vendor
from accounts.models import User




class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['vendor_name', 'vendor_license']

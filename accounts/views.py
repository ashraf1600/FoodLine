from django.shortcuts import render , HttpResponse
from .forms import UserForm
from django.shortcuts import redirect
from .models import User , UserProfile
from django.contrib import messages
from vendor.forms import VendorForm


def registerUser(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user = form.save(commit=False)
            user.set_password(password)
            user.role = User.CUSTOMER
            user.save()
            messages.error(request, 'User registered successfully.')
            return redirect(registerUser)
        else:
            print("Invalid form")
            print(form.errors)
    else:
        form = UserForm()
       
    context = {
        'form': form,   
    }

    return render(request, 'accounts/registerUser.html', context)


def registerVendor(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST, request.FILES)
        if form.is_valid() and v_form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']

            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            # user = form.save(commit=False)
            user.set_password(password)
            user.role = User.VENDOR
            user.save()
            
            vendor = v_form.save(commit=False)
            vendor.user = user
            user_profile = UserProfile.objects.get(user = user)

            vendor.user_profile =user_profile
            vendor.save()
            
            messages.success(request, 'Vendor registered successfully. Wait for the approval.')
            return redirect(registerVendor)
        else:
            print("Invalid form")
            print(form.errors)
            print(v_form.errors)
    else:
     form = UserForm()
     v_form = VendorForm()

    context = {
        'form': form,
        'v_form': v_form,
    }


    return render(request, 'accounts/registerVendor.html', context)




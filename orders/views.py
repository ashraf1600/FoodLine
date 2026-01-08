from urllib import response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from marketplace.models import Cart, Tax
from marketplace.context_processors import get_cart_amounts
from menu.models import FoodItem
from .forms import OrderForm
from .models import Order, OrderedFood, Payment
import json
from .utils import generate_order_number, order_total_by_vendor
from .sslcommerz_utils import make_payment_request, verify_payment
from accounts.utils import send_notification
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.shortcuts import get_current_site


@login_required(login_url='login')
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    vendors_ids = []
    for i in cart_items:
        if i.fooditem.vendor.id not in vendors_ids:
            vendors_ids.append(i.fooditem.vendor.id)
    
    # {"vendor_id":{"subtotal":{"tax_type": {"tax_percentage": "tax_amount"}}}}
    get_tax = Tax.objects.filter(is_active=True)
    subtotal = 0
    total_data = {}
    k = {}
    for i in cart_items:
        fooditem = FoodItem.objects.get(pk=i.fooditem.id, vendor_id__in=vendors_ids)
        v_id = fooditem.vendor.id
        if v_id in k:
            subtotal = k[v_id]
            subtotal += (fooditem.price * i.quantity)
            k[v_id] = subtotal
        else:
            subtotal = (fooditem.price * i.quantity)
            k[v_id] = subtotal
    
        # Calculate the tax_data
        tax_dict = {}
        for i in get_tax:
            tax_type = i.tax_type
            tax_percentage = i.tax_percentage
            tax_amount = round((tax_percentage * subtotal)/100, 2)
            tax_dict.update({tax_type: {str(tax_percentage) : str(tax_amount)}})
        # Construct total data
        total_data.update({fooditem.vendor.id: {str(subtotal): str(tax_dict)}})
    

        

    subtotal = get_cart_amounts(request)['subtotal']
    total_tax = get_cart_amounts(request)['tax']
    grand_total = get_cart_amounts(request)['grand_total']
    tax_data = get_cart_amounts(request)['tax_dict']
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order()
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.address = form.cleaned_data['address']
            order.country = form.cleaned_data['country']
            order.devision = form.cleaned_data['devision']
            order.city = form.cleaned_data['city']
            order.pin_code = form.cleaned_data['pin_code']
            order.user = request.user
            order.total = grand_total
            order.tax_data = json.dumps(tax_data)
            order.total_data = json.dumps(total_data)
            order.total_tax = total_tax
            order.payment_method = request.POST['payment_method']
            order.save() # order id/ pk is generated
            order.order_number = generate_order_number(order.id)
            order.vendors.add(*vendors_ids)
            order.save()

            print(f"[*] Order created: {order.order_number}")  # DEBUG
            print(f"[*] Payment method: {order.payment_method}")  # DEBUG

            # Handle SSL Commerz payment
            if order.payment_method == 'SSL_Commerz':
                print(f"[*] Initiating SSL Commerz payment...")  # DEBUG
                # Create payment request to SSL Commerz
                payment_response = make_payment_request(order)
                
                print(f"[*] Payment response: {payment_response}")  # DEBUG
                
                if payment_response['status'] == 'success':
                    print(f"[*] Redirecting to: {payment_response['redirect_url']}")  # DEBUG
                    # Redirect to SSL Commerz payment gateway
                    return redirect(payment_response['redirect_url'])
                else:
                    # Error handling
                    from django.contrib import messages
                    error_msg = f"Payment initiation failed: {payment_response['message']}"
                    print(f"[X] {error_msg}")  # DEBUG
                    messages.error(request, error_msg)
                    return redirect('checkout')

        else:
            print(f"[X] Form errors: {form.errors}")  # DEBUG
    return render(request, 'orders/place_order.html')


@login_required(login_url='login')
def payments(request):
    # Check if the request is ajax or not
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        # STORE THE PAYMENT DETAILS IN THE PAYMENT MODEL
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')

        order = Order.objects.get(user=request.user, order_number=order_number)
        payment = Payment(
            user = request.user,
            transaction_id = transaction_id,
            payment_method = payment_method,
            amount = order.total,
            status = status
        )
        payment.save()

        # UPDATE THE ORDER MODEL
        order.payment = payment
        order.is_ordered = True
        order.save()

        # MOVE THE CART ITEMS TO ORDERED FOOD MODEL
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            ordered_food = OrderedFood()
            ordered_food.order = order
            ordered_food.payment = payment
            ordered_food.user = request.user
            ordered_food.fooditem = item.fooditem
            ordered_food.quantity = item.quantity
            ordered_food.price = item.fooditem.price
            ordered_food.amount = item.fooditem.price * item.quantity # total amount
            ordered_food.save()

        # SEND ORDER CONFIRMATION EMAIL TO THE CUSTOMER
        mail_subject = 'Thank you for ordering with us.'
        mail_template = 'orders/order_confirmation_email.html'

        ordered_food = OrderedFood.objects.filter(order=order)
        customer_subtotal = 0
        for item in ordered_food:
            customer_subtotal += (item.price * item.quantity)
        tax_data = json.loads(order.tax_data)
        context = {
            'user': request.user,
            'order': order,
            'to_email': order.email,
            'ordered_food': ordered_food,
            'domain': get_current_site(request),
            'customer_subtotal': customer_subtotal,
            'tax_data': tax_data,
        }
        send_notification(mail_subject, mail_template, context)
        

        # SEND ORDER RECEIVED EMAIL TO THE VENDOR
        mail_subject = 'You have received a new order.'
        mail_template = 'orders/new_order_received.html'
        to_emails = []
        for i in cart_items:
            if i.fooditem.vendor.user.email not in to_emails:
                to_emails.append(i.fooditem.vendor.user.email)

                ordered_food_to_vendor = OrderedFood.objects.filter(order=order, fooditem__vendor=i.fooditem.vendor)
                print(ordered_food_to_vendor)

        
                context = {
                    'order': order,
                    'to_email': i.fooditem.vendor.user.email,
                    'ordered_food_to_vendor': ordered_food_to_vendor,
                    'vendor_subtotal': order_total_by_vendor(order, i.fooditem.vendor.id)['subtotal'],
                    'tax_data': order_total_by_vendor(order, i.fooditem.vendor.id)['tax_dict'],
                    'vendor_grand_total': order_total_by_vendor(order, i.fooditem.vendor.id)['grand_total'],
                }
                send_notification(mail_subject, mail_template, context)

        # CLEAR THE CART IF THE PAYMENT IS SUCCESS
        # cart_items.delete() 

        # RETURN BACK TO AJAX WITH THE STATUS SUCCESS OR FAILURE
        response = {
            'order_number': order_number,
            'transaction_id': transaction_id,
        }
        return JsonResponse(response)
    return HttpResponse('Payments view')


def order_complete(request):
    order_number = request.GET.get('order_no')
    transaction_id = request.GET.get('trans_id')

    try:
        order = Order.objects.get(order_number=order_number, payment__transaction_id=transaction_id, is_ordered=True)
        ordered_food = OrderedFood.objects.filter(order=order)

        subtotal = 0
        for item in ordered_food:
            subtotal += (item.price * item.quantity)

        tax_data = json.loads(order.tax_data)
        print(tax_data)
        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': subtotal,
            'tax_data': tax_data,
        }
        return render(request, 'orders/order_complete.html', context)
    except:
        return redirect('home')


@login_required(login_url='login')
def sslcommerz_payment(request):
    """
    Initiate SSL Commerz payment for an order
    """
    order_number = request.POST.get('order_number')
    
    try:
        order = Order.objects.get(user=request.user, order_number=order_number)
        
        # Create payment request to SSL Commerz
        payment_response = make_payment_request(order)
        
        if payment_response['status'] == 'success':
            # Store order reference temporarily (optional - for tracking)
            request.session['payment_order_number'] = order_number
            
            # Redirect to SSL Commerz payment gateway
            return JsonResponse({
                'status': 'success',
                'redirect_url': payment_response['redirect_url']
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': payment_response['message']
            })
    except Order.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@csrf_exempt
def sslcommerz_payment_success(request):
    """
    Handle successful SSL Commerz payment
    """
    tran_id = request.POST.get('tran_id')
    val_id = request.POST.get('val_id')

    print(f"[SSL SUCCESS VIEW] POST Data: {request.POST}") # DEBUG
    print(f"[SSL SUCCESS VIEW] Verify with tran_id: {tran_id}, val_id: {val_id}") # DEBUG
    
    # Verify the payment with SSL Commerz
    verification_result = verify_payment(request.POST) # Passing whole POST to be flexible
    
    if verification_result['status'] == 'success':
        transaction_data = verification_result['transaction_data']
        
        if transaction_data['status'] == 'VALID':
            try:
                order = Order.objects.get(order_number=tran_id)
                
                # Create payment record
                payment = Payment(
                    user=order.user,
                    transaction_id=tran_id,
                    payment_method='SSL_Commerz',
                    amount=order.total,
                    status='Completed'
                )
                payment.save()
                
                # Update order
                order.payment = payment
                order.is_ordered = True
                order.save()
                
                # Move cart items to ordered food
                cart_items = Cart.objects.filter(user=order.user)
                for item in cart_items:
                    ordered_food = OrderedFood(
                        order=order,
                        payment=payment,
                        user=order.user,
                        fooditem=item.fooditem,
                        quantity=item.quantity,
                        price=item.fooditem.price,
                        amount=item.fooditem.price * item.quantity
                    )
                    ordered_food.save()
                
                # Send order confirmation email to customer
                mail_subject = 'Thank you for ordering with us.'
                mail_template = 'orders/order_confirmation_email.html'
                
                ordered_food = OrderedFood.objects.filter(order=order)
                customer_subtotal = 0
                for item in ordered_food:
                    customer_subtotal += (item.price * item.quantity)
                
                tax_data = json.loads(order.tax_data)
                context = {
                    'user': order.user,
                    'order': order,
                    'to_email': order.email,
                    'ordered_food': ordered_food,
                    'domain': get_current_site(request),
                    'customer_subtotal': customer_subtotal,
                    'tax_data': tax_data,
                }
                send_notification(mail_subject, mail_template, context)
                
                # Send order received email to vendors
                mail_subject = 'You have received a new order.'
                mail_template = 'orders/new_order_received.html'
                to_emails = []
                for item in cart_items:
                    if item.fooditem.vendor.user.email not in to_emails:
                        to_emails.append(item.fooditem.vendor.user.email)
                        
                        ordered_food_to_vendor = OrderedFood.objects.filter(
                            order=order, 
                            fooditem__vendor=item.fooditem.vendor
                        )
                        
                        context = {
                            'order': order,
                            'to_email': item.fooditem.vendor.user.email,
                            'ordered_food_to_vendor': ordered_food_to_vendor,
                            'vendor_subtotal': order_total_by_vendor(order, item.fooditem.vendor.id)['subtotal'],
                            'tax_data': order_total_by_vendor(order, item.fooditem.vendor.id)['tax_dict'],
                            'vendor_grand_total': order_total_by_vendor(order, item.fooditem.vendor.id)['grand_total'],
                        }
                        send_notification(mail_subject, mail_template, context)
                
                # Clear the cart
                cart_items.delete()
                
                # Redirect to order complete page
                return redirect(f'/orders/order_complete/?order_no={order.order_number}&trans_id={tran_id}')
            except Order.DoesNotExist:
                return render(request, 'orders/payment_error.html', {
                    'message': 'Order not found'
                })
        else:
            return render(request, 'orders/payment_error.html', {
                'message': 'Payment validation failed'
            })
    else:
        return render(request, 'orders/payment_error.html', {
            'message': verification_result['message']
        })


@csrf_exempt
def sslcommerz_payment_fail(request):
    """
    Handle failed SSL Commerz payment
    """
    tran_id = request.POST.get('tran_id')
    
    try:
        order = Order.objects.get(order_number=tran_id)
        
        # Create payment record with failed status
        payment = Payment(
            user=request.user,
            transaction_id=tran_id,
            payment_method='SSL_Commerz',
            amount=order.total,
            status='Failed'
        )
        payment.save()
        
        return render(request, 'orders/payment_failed.html', {
            'order': order,
            'message': 'Payment failed. Please try again.'
        })
    except Order.DoesNotExist:
        return render(request, 'orders/payment_error.html', {
            'message': 'Order not found'
        })


@csrf_exempt
def sslcommerz_payment_cancel(request):
    """
    Handle cancelled SSL Commerz payment
    """
    tran_id = request.POST.get('tran_id')
    
    try:
        order = Order.objects.get(order_number=tran_id)
        
        return render(request, 'orders/payment_cancelled.html', {
            'order': order,
            'message': 'Payment cancelled. Please try again.'
        })
    except Order.DoesNotExist:
        return render(request, 'orders/payment_error.html', {
            'message': 'Order not found'
        })

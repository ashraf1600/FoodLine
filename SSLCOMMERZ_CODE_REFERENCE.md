# SSL Commerz Integration - Code Reference

## Key Functions Reference

### 1. make_payment_request(order)
**Location:** `orders/sslcommerz_utils.py`

```python
def make_payment_request(order):
    """
    Create a payment request to SSL Commerz
    
    Args:
        order: Order object with customer & payment details
    
    Returns:
        {
            'status': 'success',
            'redirect_url': 'https://gateway.sslcommerz.com/...'
        }
        OR
        {
            'status': 'error',
            'message': 'Error description'
        }
    
    Usage:
        response = make_payment_request(order)
        if response['status'] == 'success':
            return redirect(response['redirect_url'])
    """
```

**How it works:**
1. Collects order data (amount, customer details, etc.)
2. Creates POST request to SSL Commerz API
3. Sends store credentials
4. Receives payment gateway URL
5. Returns URL for redirect

**Data sent to SSL Commerz:**
- store_id
- store_passwd  
- total_amount
- currency (BDT)
- tran_id (order number)
- callback URLs (success, fail, cancel)
- Customer info (name, email, phone, address)

---

### 2. verify_payment(tran_id)
**Location:** `orders/sslcommerz_utils.py`

```python
def verify_payment(tran_id):
    """
    Verify payment transaction with SSL Commerz
    
    Args:
        tran_id: Transaction ID from SSL Commerz callback
    
    Returns:
        {
            'status': 'success',
            'transaction_data': {
                'tran_id': '...',
                'status': 'VALID',
                'amount': '1500.00',
                ...
            }
        }
        OR
        {
            'status': 'error',
            'message': 'Error description'
        }
    
    Usage:
        verification = verify_payment(tran_id)
        if verification['status'] == 'success':
            trans_data = verification['transaction_data']
            if trans_data['status'] == 'VALID':
                # Payment is valid, proceed
    """
```

**Important:** Always verify payment before marking order as paid!

---

### 3. place_order(request) - UPDATED
**Location:** `orders/views.py`

```python
@login_required(login_url='login')
def place_order(request):
    """
    Create order and handle payment gateway redirect
    
    For SSL Commerz:
    1. Validates form data
    2. Creates Order object
    3. Calls make_payment_request()
    4. Redirects to payment gateway
    
    For other methods:
    1. Creates Order object  
    2. Returns to checkout page
    """
```

**Key addition:**
```python
if order.payment_method == 'SSL_Commerz':
    payment_response = make_payment_request(order)
    if payment_response['status'] == 'success':
        return redirect(payment_response['redirect_url'])
```

---

### 4. sslcommerz_payment_success(request)
**Location:** `orders/views.py`

```python
@login_required(login_url='login')
def sslcommerz_payment_success(request):
    """
    Handle successful SSL Commerz payment
    
    Flow:
    1. Gets tran_id & val_id from SSL Commerz POST
    2. Verifies payment with SSL Commerz API
    3. Creates Payment record in database
    4. Updates Order (is_ordered=True)
    5. Moves cart items to OrderedFood
    6. Sends confirmation email to customer
    7. Sends order notification to vendors
    8. Clears shopping cart
    9. Redirects to order complete page
    
    Returns:
        - Redirect to order_complete page on success
        - Renders payment_error.html on failure
    """
```

**What happens:**
1. Payment verified with API
2. Payment model created
3. Order marked as paid
4. Cart cleared
5. Emails sent
6. Order complete page shown

---

### 5. sslcommerz_payment_fail(request)
**Location:** `orders/views.py`

```python
@login_required(login_url='login')
def sslcommerz_payment_fail(request):
    """
    Handle failed SSL Commerz payment
    
    Flow:
    1. Gets tran_id from SSL Commerz POST
    2. Finds Order from tran_id
    3. Creates Payment record with 'Failed' status
    4. Shows payment_failed.html template
    5. Allows user to retry
    """
```

---

### 6. sslcommerz_payment_cancel(request)
**Location:** `orders/views.py`

```python
@login_required(login_url='login')
def sslcommerz_payment_cancel(request):
    """
    Handle cancelled SSL Commerz payment
    
    When user clicks "Cancel" on payment gateway
    
    Flow:
    1. Gets tran_id from SSL Commerz POST
    2. Finds Order from tran_id
    3. Shows payment_cancelled.html template
    4. Cart items remain available
    5. User can retry payment
    """
```

---

## How to Customize

### Change callback URLs:

**File:** `orders/sslcommerz_utils.py`

```python
'success_url': f'http://localhost:8000/orders/sslcommerz/success/',
'fail_url': f'http://localhost:8000/orders/sslcommerz/fail/',
'cancel_url': f'http://localhost:8000/orders/sslcommerz/cancel/',
```

For production, update to your domain:
```python
'success_url': f'https://yourdomain.com/orders/sslcommerz/success/',
'fail_url': f'https://yourdomain.com/orders/sslcommerz/fail/',
'cancel_url': f'https://yourdomain.com/orders/sslcommerz/cancel/',
```

### Change payment descriptions:

**File:** `orders/sslcommerz_utils.py`

```python
'product_name': 'Food Order',  # Change this
'product_category': 'Food Delivery',  # Or this
```

### Customize email templates:

**Customer email:** `templates/orders/order_confirmation_email.html`
**Vendor email:** `templates/orders/new_order_received.html`

---

## Error Handling Examples

### Example 1: Payment initiation fails

```python
# In place_order view
payment_response = make_payment_request(order)

if payment_response['status'] == 'success':
    return redirect(payment_response['redirect_url'])
else:
    messages.error(request, f"Payment failed: {payment_response['message']}")
    return redirect('checkout')
```

### Example 2: Verification fails

```python
# In sslcommerz_payment_success view
verification_result = verify_payment(tran_id)

if verification_result['status'] != 'success':
    return render(request, 'orders/payment_error.html', {
        'message': verification_result['message']
    })
```

### Example 3: Order not found

```python
try:
    order = Order.objects.get(order_number=tran_id)
except Order.DoesNotExist:
    return render(request, 'orders/payment_error.html', {
        'message': 'Order not found'
    })
```

---

## Testing Code Examples

### Test 1: Manual payment verification

```python
# In Django shell
python manage.py shell

from orders.sslcommerz_utils import verify_payment
result = verify_payment('ORDER_NUMBER')
print(result)
```

### Test 2: Create test order manually

```python
from orders.models import Order
from accounts.models import User

user = User.objects.first()
order = Order(
    user=user,
    first_name='Test',
    last_name='User',
    email='test@example.com',
    phone='01712345678',
    address='Test Address',
    city='Dhaka',
    pin_code='1000',
    country='Bangladesh',
    total=1500.00,
    payment_method='SSL_Commerz',
    order_number='TEST123'
)
order.save()
```

### Test 3: Simulate payment success

```python
from orders.models import Payment, Order
from django.utils import timezone

# Get order
order = Order.objects.get(order_number='ORDER_123')

# Create payment
payment = Payment(
    user=order.user,
    transaction_id='TEST_TXN_123',
    payment_method='SSL_Commerz',
    amount=order.total,
    status='Completed'
)
payment.save()

# Update order
order.payment = payment
order.is_ordered = True
order.save()

print(f"Order {order.order_number} marked as paid")
```

---

## Common Issues & Solutions

### Issue 1: Payment gateway redirects but comes back empty

**Solution:** Check callback URLs are correct
```python
# In sslcommerz_utils.py, verify:
'success_url': 'http://localhost:8000/orders/sslcommerz/success/',  # Exact match required
```

### Issue 2: Order not found on callback

**Solution:** Verify order was created before redirect
```python
# In place_order view, add logging:
print(f"Order created: {order.order_number}")
```

### Issue 3: Email not sending

**Solution:** Check email configuration
```python
# In settings.py, verify:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your provider
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your@email.com'
EMAIL_HOST_PASSWORD = 'your_password'
```

### Issue 4: Cart not clearing after payment

**Solution:** Check Cart model query
```python
# In sslcommerz_payment_success():
cart_items = Cart.objects.filter(user=request.user)
cart_items.delete()  # Make sure this executes
```

---

## Debugging Tips

### Enable debug logging:

```python
# In orders/views.py, add:
import logging
logger = logging.getLogger(__name__)

# In payment handlers:
logger.info(f"Processing payment for order: {order.order_number}")
logger.debug(f"Payment response: {payment_response}")
logger.error(f"Payment failed: {error_message}")
```

### Print to console for testing:

```python
print(f"Order: {order.order_number}")
print(f"Total: {order.total}")
print(f"Payment response: {payment_response}")
```

### Check database queries:

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as queries:
    # Your code here
    pass

print(f"Queries: {len(queries)}")
for query in queries:
    print(query['sql'])
```

---

## Performance Optimization

### Cache order lookups:

```python
from django.core.cache import cache

# In sslcommerz_payment_success():
cache_key = f'order_{tran_id}'
order = cache.get(cache_key)
if not order:
    order = Order.objects.get(order_number=tran_id)
    cache.set(cache_key, order, 3600)  # Cache for 1 hour
```

### Bulk create OrderedFood:

```python
# Instead of loop
ordered_foods = [
    OrderedFood(
        order=order,
        payment=payment,
        user=request.user,
        fooditem=item.fooditem,
        quantity=item.quantity,
        price=item.fooditem.price,
        amount=item.fooditem.price * item.quantity
    )
    for item in cart_items
]
OrderedFood.objects.bulk_create(ordered_foods)
```

---

## Security Checklist

- ✅ Always verify payment with API
- ✅ Use HTTPS in production
- ✅ Validate order data before processing
- ✅ Check user authentication
- ✅ Log all transactions
- ✅ Never trust client-side payment status
- ✅ Implement CSRF protection
- ✅ Sanitize user inputs
- ✅ Rate-limit payment endpoints
- ✅ Monitor for fraud patterns


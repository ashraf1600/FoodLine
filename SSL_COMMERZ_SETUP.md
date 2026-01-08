# SSL Commerz Integration Setup Guide

## Installation Steps

### 1. Install Required Package
```bash
pip install requests
```

The `requests` library is used to communicate with the SSL Commerz API.

### 2. Verify Settings (Already Done)
Your `settings.py` already contains:
```python
SSLCOMMERZ_STORE_ID = "multi6945960959830"
SSLCOMMERZ_STORE_PASS = "multi6945960959830@ssl"
SSLCOMMERZ_IS_LIVE = False  # Sandbox mode - set to True for production
```

### 3. Add SSL Commerz Logo
Place the SSL Commerz logo image at:
```
static/images/sslcommerz-logo.png
```
You can download it from: https://www.sslcommerz.com/

## How It Works

### Payment Flow:

1. **Customer selects SSL Commerz** at checkout
2. **Clicks "PLACE ORDER"** → Order created in database
3. **System initiates SSL Commerz payment** → Redirects to payment gateway
4. **Customer makes payment** on SSL Commerz
5. **Payment callback** → System receives success/fail/cancel response
6. **Order confirmation emails** sent to customer and vendors
7. **Order marked as complete** → Customer sees order confirmation page

### Files Modified/Created:

**Modified:**
- `orders/models.py` - Added SSL Commerz to PAYMENT_METHOD choices
- `orders/urls.py` - Added SSL Commerz payment routes
- `orders/views.py` - Added SSL Commerz payment handler functions
- `templates/marketplace/checkout.html` - Added SSL Commerz payment option

**Created:**
- `orders/sslcommerz_utils.py` - SSL Commerz API integration
- `templates/orders/payment_failed.html` - Failed payment page
- `templates/orders/payment_cancelled.html` - Cancelled payment page
- `templates/orders/payment_error.html` - Error handling page

## Testing

### Sandbox Mode (Current):
- Use test card: **4111111111111111**
- Expiry: Any future date
- CVV: Any 3 digits
- Store ID: multi6945960959830
- Store Password: multi6945960959830@ssl

### Production Mode:
Change in settings.py:
```python
SSLCOMMERZ_IS_LIVE = True
```
And update with your real store credentials.

## API Endpoints

The system uses these SSL Commerz endpoints:

- **Sandbox:** `https://sandbox.sslcommerz.com/gwprocess/v4/api.php`
- **Live:** `https://securepay.sslcommerz.com/gwprocess/v4/api.php`

## Callback URLs

These URLs are automatically set in payment requests:
- Success: `http://localhost:8000/orders/sslcommerz/success/`
- Fail: `http://localhost:8000/orders/sslcommerz/fail/`
- Cancel: `http://localhost:8000/orders/sslcommerz/cancel/`

**Note:** For production, update `localhost:8000` to your actual domain.

## Troubleshooting

### Payment not working?
1. Check SSLCOMMERZ_STORE_ID and SSLCOMMERZ_STORE_PASS in settings.py
2. Ensure `requests` package is installed: `pip install requests`
3. Check Django logs for errors
4. Verify callback URLs are reachable from SSL Commerz

### Order not created?
1. Ensure cart has items before checkout
2. Check all required fields are filled in checkout form
3. Check database connection

### Email not sending?
1. Verify email configuration in Django settings
2. Check that `send_notification` function is working
3. Review email templates in `templates/orders/`

## Production Checklist

- [ ] Update `SSLCOMMERZ_IS_LIVE` to `True`
- [ ] Update store credentials for production
- [ ] Update callback URLs to your actual domain
- [ ] Test with real payment
- [ ] Configure HTTPS (SSL certificate)
- [ ] Set up email with proper SMTP credentials
- [ ] Test order confirmation emails

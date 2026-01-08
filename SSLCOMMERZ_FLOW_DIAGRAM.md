# SSL Commerz Payment Flow Diagram

## Complete Payment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      CUSTOMER JOURNEY                            │
└─────────────────────────────────────────────────────────────────┘

1️⃣  ADD ITEMS TO CART
    ├─ Browse food items
    ├─ Add quantity
    └─ Click "Add to Cart"
           ↓

2️⃣  PROCEED TO CHECKOUT
    ├─ View cart summary
    ├─ See subtotal & taxes
    └─ Click "Checkout"
           ↓

3️⃣  FILL CUSTOMER DETAILS (checkout.html)
    ├─ First Name
    ├─ Last Name
    ├─ Email
    ├─ Phone
    ├─ Address
    ├─ City/Division
    └─ Pin Code
           ↓

4️⃣  SELECT PAYMENT METHOD
    ├─ ○ Bkash
    ├─ ○ PayPal
    └─ ○ SSL Commerz  ← SELECT THIS
           ↓

5️⃣  CLICK "PLACE ORDER" BUTTON
           ↓
    ┌────────────────────────────┐
    │  BACKEND PROCESSING        │
    │  place_order() view        │
    │  ├─ Validate form         │
    │  ├─ Create Order object   │
    │  ├─ Generate order number │
    │  ├─ Save to database      │
    │  └─ Call make_payment()   │
    └────────────────────────────┘
           ↓

6️⃣  PAYMENT GATEWAY REQUEST
    ┌──────────────────────────────────────────┐
    │ sslcommerz_utils.py                      │
    │ make_payment_request(order)              │
    │ ├─ POST to SSL Commerz API              │
    │ ├─ Send: order details, amounts        │
    │ ├─ Receive: payment gateway URL        │
    │ └─ Return redirect URL                 │
    └──────────────────────────────────────────┘
           ↓

7️⃣  REDIRECT TO SSL COMMERZ PAYMENT GATEWAY
    https://sandbox.sslcommerz.com/gwprocess/...
           ↓
    ┌──────────────────────────────┐
    │  SSL COMMERZ PAYMENT PAGE    │
    │  ├─ Show order details       │
    │  ├─ Request card details     │
    │  ├─ Process payment          │
    │  └─ Generate transaction ID  │
    └──────────────────────────────┘
           ↓

8️⃣  CUSTOMER ENTERS PAYMENT DETAILS
    ├─ Card Number: 4111111111111111
    ├─ Expiry: MM/YY
    ├─ CVV: 3 digits
    └─ Click Pay
           ↓

9️⃣  PAYMENT PROCESSING
    ├─ Validate card details
    ├─ Process transaction
    ├─ Generate confirmation
    └─ Prepare callback
           ↓

🔟 PAYMENT CALLBACK
   SSL Commerz sends POST to your server
   ┌─────────────────────────────────┐
   │ Callback Response Options:       │
   │ ├─ Success (VALID)             │
   │ ├─ Failed (FAILED/CANCELLED)   │
   │ └─ Pending (PENDING)           │
   └─────────────────────────────────┘
           ↓
   ┌──────────────────────────────────────────┐
   │ IF PAYMENT SUCCESS:                      │
   │ /orders/sslcommerz/success/              │
   └──────────────────────────────────────────┘
           ↓
    ┌────────────────────────────────────────┐
    │ sslcommerz_payment_success() view      │
    │                                        │
    │ ✓ Verify payment with SSL Commerz     │
    │ ✓ Create Payment record               │
    │ ✓ Update Order (is_ordered=True)      │
    │ ✓ Move Cart items to OrderedFood      │
    │ ✓ Send confirmation email to customer│
    │ ✓ Send order email to vendors        │
    │ ✓ Clear shopping cart                │
    │ ✓ Redirect to order complete page    │
    └────────────────────────────────────────┘
           ↓

1️⃣1️⃣ ORDER COMPLETE PAGE
    ├─ Show: Order Number
    ├─ Show: Order Items
    ├─ Show: Total Amount
    ├─ Show: Delivery Address
    ├─ Show: Status: "Paid ✓"
    └─ Button: "Continue Shopping" / "View Order"


┌─────────────────────────────────────────────────────────────────┐
│                      IF PAYMENT FAILS                            │
└─────────────────────────────────────────────────────────────────┘

   ├─ /orders/sslcommerz/fail/
   │  └─ Show payment failed page
   │     └─ Offer to retry
   │
   └─ /orders/sslcommerz/cancel/
      └─ Show payment cancelled page
         └─ Cart items still available


┌─────────────────────────────────────────────────────────────────┐
│                    EMAIL NOTIFICATIONS                           │
└─────────────────────────────────────────────────────────────────┘

CUSTOMER EMAIL:
├─ Subject: "Thank you for ordering with us"
├─ Content:
│  ├─ Order Number
│  ├─ Items ordered with prices
│  ├─ Subtotal
│  ├─ Taxes breakdown
│  ├─ Grand Total
│  └─ Delivery Address

VENDOR EMAILS (One per vendor):
├─ Subject: "You have received a new order"
├─ Content:
│  ├─ Order Number
│  ├─ Items for THIS vendor only
│  ├─ Vendor-specific subtotal & taxes
│  ├─ Vendor grand total
│  └─ Customer delivery address


┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE CHANGES                              │
└─────────────────────────────────────────────────────────────────┘

ORDERS TABLE:
├─ order_number: Generated unique ID
├─ user_id: Customer who placed order
├─ payment_id: Link to Payment record
├─ payment_method: "SSL_Commerz"
├─ first_name: From form
├─ last_name: From form
├─ email: From form
├─ phone: From form
├─ address: From form
├─ city: From form
├─ pin_code: From form
├─ total: Total amount including tax
├─ is_ordered: TRUE (after payment)
├─ status: "New" → "Accepted" (by vendor)
└─ created_at: Timestamp

PAYMENTS TABLE:
├─ user_id: Customer
├─ transaction_id: From SSL Commerz
├─ payment_method: "SSL_Commerz"
├─ amount: Total amount
├─ status: "Completed" (after success)
└─ created_at: Timestamp

ORDERED_FOOD TABLE:
├─ order_id: Which order
├─ payment_id: Payment record
├─ user_id: Customer
├─ fooditem_id: What was ordered
├─ quantity: How many
├─ price: Unit price
└─ amount: quantity × price

CART TABLE:
├─ CLEARED after successful payment
├─ All items moved to OrderedFood
└─ Ready for new shopping session


┌─────────────────────────────────────────────────────────────────┐
│                    API COMMUNICATION                             │
└─────────────────────────────────────────────────────────────────┘

REQUEST TO SSL COMMERZ:
POST /api/v4/merchantRequest/

Data Sent:
├─ store_id: "multi6945960959830"
├─ store_passwd: "multi6945960959830@ssl"
├─ total_amount: "1500.00"
├─ currency: "BDT"
├─ tran_id: ORDER_NUMBER
├─ success_url: "http://localhost:8000/orders/sslcommerz/success/"
├─ fail_url: "http://localhost:8000/orders/sslcommerz/fail/"
├─ cancel_url: "http://localhost:8000/orders/sslcommerz/cancel/"
├─ cus_name: Customer name
├─ cus_email: Customer email
├─ cus_phone: Customer phone
├─ cus_add1: Address
├─ cus_city: City
├─ cus_country: Country
├─ product_name: "Food Order"
└─ product_category: "Food Delivery"

RESPONSE FROM SSL COMMERZ:
├─ status: "success"
├─ GatewayPageURL: Payment gateway URL
└─ sessionkey: Session ID

VERIFICATION REQUEST:
POST /api/v4/transaction/query/general/

Data:
├─ store_id: "multi6945960959830"
├─ store_passwd: "multi6945960959830@ssl"
└─ tran_id: TRANSACTION_ID

VERIFICATION RESPONSE:
├─ element_transactions: [
│  ├─ tran_id: Transaction ID
│  ├─ status: "VALID" or "FAILED"
│  ├─ amount: Paid amount
│  ├─ currency: "BDT"
│  └─ ...
│  ]


┌─────────────────────────────────────────────────────────────────┐
│                    URL ROUTING                                   │
└─────────────────────────────────────────────────────────────────┘

URLS.PY ROUTES:

POST  /orders/place_order/          → place_order() view
POST  /orders/payments/             → payments() view
GET   /orders/order_complete/       → order_complete() view

GET   /orders/sslcommerz/payment/   → sslcommerz_payment() view
POST  /orders/sslcommerz/success/   → sslcommerz_payment_success()
POST  /orders/sslcommerz/fail/      → sslcommerz_payment_fail()
POST  /orders/sslcommerz/cancel/    → sslcommerz_payment_cancel()


┌─────────────────────────────────────────────────────────────────┐
│                    FILE STRUCTURE                                │
└─────────────────────────────────────────────────────────────────┘

orders/
├─ models.py ......................... Payment model with SSL_Commerz
├─ views.py .......................... 4 SSL Commerz handler views
├─ urls.py ........................... 4 SSL Commerz routes
├─ sslcommerz_utils.py .............. API integration (NEW)
└─ forms.py .......................... Order form

templates/
├─ marketplace/
│  └─ checkout.html .................. Payment method selection
└─ orders/
   ├─ payment_success.html (implicit)
   ├─ payment_failed.html ............ Payment failed page (NEW)
   ├─ payment_cancelled.html ......... Payment cancelled page (NEW)
   ├─ payment_error.html ............ Error handling page (NEW)
   └─ order_complete.html


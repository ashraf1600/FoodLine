import requests
import hashlib
from foodOnline_main.settings import SSLCOMMERZ_STORE_ID, SSLCOMMERZ_STORE_PASS, SSLCOMMERZ_IS_LIVE


def make_payment_request(order):
    """
    Create a payment request to SSL Commerz
    Returns the payment URL or error message
    """
    
    # Determine the API endpoint
    if SSLCOMMERZ_IS_LIVE:
        api_url = 'https://securepay.sslcommerz.com/gwprocess/v4/api.php'
    else:
        api_url = 'https://sandbox.sslcommerz.com/gwprocess/v4/api.php'
    
    print(f"[SSL Commerz] API URL: {api_url}")  # DEBUG
    
    # Prepare the payment request data
    post_data = {
        'store_id': SSLCOMMERZ_STORE_ID,
        'store_passwd': SSLCOMMERZ_STORE_PASS,
        'total_amount': str(order.total),
        'currency': 'BDT',
        'tran_id': order.order_number,  # Unique transaction ID
        'success_url': f'http://localhost:8000/orders/sslcommerz/success/',
        'fail_url': f'http://localhost:8000/orders/sslcommerz/fail/',
        'cancel_url': f'http://localhost:8000/orders/sslcommerz/cancel/',
        'emi_option': '0',
        'cus_name': order.first_name + ' ' + order.last_name,
        'cus_email': order.email,
        'cus_add1': order.address,
        'cus_add2': order.city,
        'cus_city': order.city,
        'cus_state': order.devision,
        'cus_postcode': order.pin_code,
        'cus_country': order.country,
        'cus_phone': order.phone,
        'shipping_method': 'NO',
        'product_name': 'Food Order',
        'product_category': 'Food Delivery',
        'product_profile': 'food',
    }
    
    print(f"[SSL Commerz] Sending request with data: {post_data}")  # DEBUG
    
    try:
        # Make the request to SSL Commerz
        response = requests.post(api_url, data=post_data)
        
        print(f"[SSL Commerz] Response status: {response.status_code}")  # DEBUG
        print(f"[SSL Commerz] Response text: {response.text}")  # DEBUG
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"[SSL Commerz] Response JSON: {result}")  # DEBUG
            
            if result.get('status') == 'success' or result.get('status') == 'SUCCESS':
                # Return the GatewayPageURL for redirect
                redirect_url = result.get('GatewayPageURL')
                print(f"[SSL Commerz] [OK] Success! Redirect URL: {redirect_url}")  # DEBUG
                return {
                    'status': 'success',
                    'redirect_url': redirect_url
                }
            else:
                error_msg = result.get('failedreason', 'Payment initialization failed')
                print(f"[SSL Commerz] [X] Failed: {error_msg} | Response: {result}")  # DEBUG
                return {
                    'status': 'error',
                    'message': error_msg
                }
        else:
            error_msg = 'Failed to connect to payment gateway'
            print(f"[SSL Commerz] [X] {error_msg}")  # DEBUG
            return {
                'status': 'error',
                'message': error_msg
            }
    except Exception as e:
        error_msg = str(e)
        print(f"[SSL Commerz] [X] Exception: {error_msg}")  # DEBUG
        return {
            'status': 'error',
            'message': error_msg
        }


def verify_payment(payment_data):
    """
    Verify the payment transaction with SSL Commerz
    Args:
        payment_data: Dictionary containing 'val_id' (preferred) or 'tran_id', 
                      OR a string representing 'tran_id'
    """
    
    # Determine mode (Live/Sandbox)
    if SSLCOMMERZ_IS_LIVE:
        base_url = 'https://securepay.sslcommerz.com'
    else:
        base_url = 'https://sandbox.sslcommerz.com'

    # Handle input type (dict or str)
    val_id = None
    tran_id = None
    
    if isinstance(payment_data, dict):
        val_id = payment_data.get('val_id')
        tran_id = payment_data.get('tran_id')
    else:
        tran_id = str(payment_data)

    print(f"[SSL Verify] Verifying payment. val_id: {val_id}, tran_id: {tran_id}") # DEBUG

    # Method 1: Validation by val_id (Preferred for success callbacks)
    if val_id:
        validation_url = f"{base_url}/validator/api/validationserverAPI.php"
        params = {
            'val_id': val_id,
            'store_id': SSLCOMMERZ_STORE_ID,
            'store_passwd': SSLCOMMERZ_STORE_PASS,
            'format': 'json'
        }
        
        print(f"[SSL Verify] Requesting Validation API: {validation_url}") # DEBUG
        try:
            response = requests.get(validation_url, params=params)
            print(f"[SSL Verify] Response Status: {response.status_code}") # DEBUG
            
            if response.status_code == 200:
                result = response.json()
                print(f"[SSL Verify] Response JSON: {result}") # DEBUG
                
                if result.get('status') == 'VALID' or result.get('status') == 'VALIDATED':
                    return {
                        'status': 'success',
                        'transaction_data': result
                    }
                else:
                     return {
                        'status': 'error',
                        'message': f"Validation Failed: {result.get('status')} - {result.get('failedreason', 'Unknown reason')}"
                    }
        except Exception as e:
            print(f"[SSL Verify] Exception: {e}") # DEBUG
            return {'status': 'error', 'message': str(e)}

    # Method 2: Validation by Transaction ID (Fallback)
    elif tran_id:
        validation_url = f"{base_url}/validator/api/merchantTransIDvalidationAPI.php"
        params = {
            'tran_id': tran_id,
            'store_id': SSLCOMMERZ_STORE_ID,
            'store_passwd': SSLCOMMERZ_STORE_PASS,
            'format': 'json'
        }
        
        print(f"[SSL Verify] Requesting Transaction Query API: {validation_url}") # DEBUG
        try:
            response = requests.get(validation_url, params=params)
            print(f"[SSL Verify] Response Status: {response.status_code}") # DEBUG
            
            if response.status_code == 200:
                result = response.json()
                print(f"[SSL Verify] Response JSON: {result}") # DEBUG

                if result.get('element_transactions'):
                     # The API returns a list of transactions for this ID (usually one)
                    transaction = result['element_transactions'][0]
                    if transaction.get('status') == 'VALID' or transaction.get('status') == 'VALIDATED':
                         return {
                            'status': 'success',
                            'transaction_data': transaction
                        }
                    else:
                         return {
                            'status': 'error',
                            'message': f"Transaction status: {transaction.get('status')}"
                        }
                elif result.get('no_of_trans_found') == 0:
                     return {
                        'status': 'error',
                        'message': 'Transaction not found'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Invalid response structure'
                    }
        except Exception as e:
             print(f"[SSL Verify] Exception: {e}") # DEBUG
             return {'status': 'error', 'message': str(e)}

    return {
        'status': 'error',
        'message': 'No transaction ID or Validation ID provided'
    }

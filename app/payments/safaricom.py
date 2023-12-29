# In a module (e.g., safaricom.py)
import requests
from flask import current_app

def generate_token():
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    auth = (current_app.config['SAFARICOM_API_KEY'], current_app.config['SAFARICOM_API_SECRET'])
    response = requests.get(api_url, auth=auth)
    return response.json().get('access_token')

def lipa_na_mpesa_online(order_id, amount, phone_number):
    token = generate_token()
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'BusinessShortCode': current_app.config['SAFARICOM_SHORTCODE'],
        'Password': current_app.config['SAFARICOM_LNM_PASSKEY'],
        'Timestamp': datetime.now().strftime('%Y%m%d%H%M%S'),
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone_number,
        'PartyB': current_app.config['SAFARICOM_SHORTCODE'],
        'PhoneNumber': phone_number,
        'CallBackURL': current_app.config['SAFARICOM_LNM_CALLBACK_URL'],
        'AccountReference': order_id,
        'TransactionDesc': 'Payment for Order',
    }
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

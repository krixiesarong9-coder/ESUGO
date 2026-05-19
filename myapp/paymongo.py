import base64
import requests
from django.conf import settings

PAYMONGO_BASE_URL = "https://api.paymongo.com/v1"


def get_auth_header():

    secret = settings.PAYMONGO_SECRET_KEY

    encoded = base64.b64encode(
        f"{secret}:".encode()
    ).decode()

    return {
        "Authorization": f"Basic {encoded}"
    }


def create_payment_link(amount, description, redirect_url):

    headers = {
        **get_auth_header(),
        "Content-Type": "application/json"
    }

    payload = {
        "data": {
            "attributes": {
                "amount": amount,
                "description": description,
                "currency": "PHP",
                "redirect": {
                    "success": redirect_url + "?status=success",
                    "failed": redirect_url + "?status=failed",
                }
            }
        }
    }

    response = requests.post(
        f"{PAYMONGO_BASE_URL}/links",
        json=payload,
        headers=headers
    )

    response.raise_for_status()

    data = response.json()["data"]

    return {
        "link_id": data["id"],
        "checkout_url": data["attributes"]["checkout_url"]
    }


def create_checkout_session(amount, description, redirect_url, payment_method_types):
    headers = {
        **get_auth_header(),
        "Content-Type": "application/json"
    }

    payload = {
        "data": {
            "attributes": {
                "description": description,
                "line_items": [
                    {
                        "currency": "PHP",
                        "amount": amount,
                        "name": description,
                        "quantity": 1
                    }
                ],
                "payment_method_types": payment_method_types,
                "success_url": redirect_url + "?status=success",
                "cancel_url": redirect_url + "?status=failed",
                "send_email_receipt": False,
                "show_description": True,
                "show_line_items": True
            }
        }
    }

    response = requests.post(
        f"{PAYMONGO_BASE_URL}/checkout_sessions",
        json=payload,
        headers=headers
    )

    response.raise_for_status()

    data = response.json()["data"]

    return {
        "checkout_session_id": data["id"],
        "checkout_url": data["attributes"]["checkout_url"]
    }

# Checkout Verification Webhook

## Overview

The `checkout.verification` webhook is sent when a bank payment is matched to a checkout during statement reconciliation. It provides **encrypted payer account details** (name and IBAN) that you can use for identity verification.

This webhook is only triggered for bank-based payment methods (bank transfer, bank button, PISP).

> [!NOTE]
> To enable this webhook, contact us to activate the `webhook_verification` feature on your account.

## Webhook payload

```json
{
    "external_id": "74775d02-745f-4198-cf3c-be9f1971dabe",
    "object": "webhook",
    "type": "checkout.verification",
    "data": {
        "object": "checkout",
        "id": 141209,
        "external_id": "74775d02-745f-4198-cf3c-be9f1971dabe",
        "amount": 300,
        "currency": "EUR",
        "redirect_url": "https://some-eshop.local/merchant_redirect_url",
        "customer": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@payout.one",
            "iban": null
        },
        "account_details": {
            "name": "<encrypted>",
            "iban": "<encrypted>"
        },
        "payment": {
            "object": "payment",
            "status": "successful",
            "payment_method": "bank_transfer",
            "failure_reason": "",
            "created_at": 1635412755,
            "fee": 8,
            "net": 292
        },
        "metadata": null,
        "status": "succeeded",
        "is_status_final": true
    },
    "nonce": "QjJqWEtiVDBNSmMyTm11dg",
    "signature": "f3b8264f42930eff215c6570f4bcdd50bcedcaf3c6da8ccfd301c6de41f36607"
}
```

The `account_details.name` and `account_details.iban` fields contain AES-256-CBC encrypted payer details from the bank statement. See [Decrypting account details](#decrypting-account-details) below.

## Signature verification

Same as for other webhooks. Canonical string:
```
external_id|type|nonce|client_secret
```
Hash with **SHA256**, encode **Base16 lowercase**.

## Decrypting account details

1. Derive the key: `lowercase(hex(SHA512(client_id)))[0..31]`
2. Base64-decode the encrypted value
3. First 16 bytes = IV, rest = ciphertext
4. Decrypt with AES-256-CBC, remove PKCS7 padding

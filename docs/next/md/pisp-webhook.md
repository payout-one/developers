# PIS Payments Status Webhook

## Overview

Notify us when an order’s status changes by sending a **signed** JSON payload.
`data.resource_id` must be your `checkout.id`.

**Use Cases:**

* Payment confirmation (`completed`)
* Intermediate states (`pending`, etc.)
* Failure notifications (`failed`, `canceled`, `refunded`)

## How It Works

When your system updates an order status:

1. Generate a **nonce** (Base64 of 16+ cryptographically random bytes).
2. Build the **canonical string** in this exact order with `|` separators:
   `resource_id|status|nonce|client_id`
3. Compute `signature = base64(HMAC_SHA256(api_key, canonical_string))`.
4. Send a `POST` request with the JSON body described below.

## Endpoint

```
POST https://{our-domain}/api/v1/acquirer/pisp_status
Content-Type: application/json
```

> `{our-domain}` is provided during onboarding.

## Authentication

Use HMAC-SHA256 with a partner-specific secret.

**Canonical String (exact order, no extra spaces):**

```
resource_id|status|nonce|client_id
```

**Signature (pseudocode):**

```
inputs:
  api_key     // secret we gave you
  resource_id // your checkout.id
  status
  nonce       // Base64(16+ random bytes), unique per request
  client_id   // the ID we assigned to you

payload_string = resource_id + "|" + status + "|" + nonce + "|" + client_id
raw_hmac = HMAC_SHA256(key=api_key, message=payload_string)   // bytes
signature = BASE64_ENCODE(raw_hmac)
```

Include `signature` at the **top level** of the JSON body.

## Request Body

```json
{
  "type": "order_status",
  "data": {
    "resource_id": "chk_123456789",   // your checkout.id
    "status": "completed",
    "nonce": "bC8w3o7M0y7o0t4cC8h3jg==",
    "client_id": "partner-xyz" // your account id
  },
  "signature": "k9MskmD8gHqFjZ/X1Cq5syruw7EjDq+Nvm7Ct60hJpQ="
}
```

⚠️ **Important:** The canonical string must match the body values exactly and use `|` separators with no whitespace.

## Example Request

```bash
POST /api/v1/acquirer/pisp_status
Host: {our-domain}
Content-Type: application/json

{
  "type": "order_status",
  "data": {
    "resource_id": "12345",
    "status": "completed",
    "nonce": "bC8w3o7M0y7o0t4cC8h3jg==",
    "client_id": "123"
  },
  "signature": "k9MskmD8gHqFjZ/X1Cq5syruw7EjDq+Nvm7Ct60hJpQ="
}
```

## Responses

**Successful**

```json
{ "status": "ok" }
```

**Missing signature**

```json
{ "error": "missing_signature", "message": "Signature must be provided" }
```

**Invalid signature**

```json
{ "error": "invalid_signature", "message": "Signature verification failed" }
```

**Unknown resource**

```json
{ "error": "not_found", "message": "Resource does not exist" }
```

**Invalid payload**

```json
{ "error": "invalid_payload" }
```

## Field Notes

* **`resource_id`** — your `checkout.id` (opaque string).
* **`status`** — use values from your system; `"completed"` denotes success.
* **`nonce`** — must be unique per request (Base64 of 16+ random bytes).
* **`client_id`** — your account id.
* **Encoding** — JSON UTF-8; standard Base64 (not URL-safe).

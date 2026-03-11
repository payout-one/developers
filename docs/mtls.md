# mTLS (Mutual TLS) Authentication

Payout API v2 endpoints are secured with mutual TLS (mTLS) authentication. This provides an additional layer of security beyond standard Bearer token authentication — every API call must be accompanied by a valid client certificate issued by Payout.

## Overview

mTLS ensures that both the server and the client verify each other's identity during the TLS handshake. This means:

- The **server** presents its certificate to the client (standard HTTPS).
- The **client** presents its certificate to the server, proving its identity.

Only requests with a valid client certificate that is registered to your API key will be accepted on `/api/v2` endpoints.

## How It Works

1. You generate a private key and a Certificate Signing Request (CSR).
2. You upload the CSR via the Payout Merchant Portal.
3. Payout signs your CSR with its Certificate Authority (CA) and returns a signed client certificate.
4. You use the signed certificate and your private key when making API calls to `/api/v2` endpoints.

The server verifies:
- **TLS layer (nginx):** The client certificate is signed by the Payout CA and the client possesses the corresponding private key.
- **Application layer:** The certificate fingerprint matches the one registered to your API key.

## Setup

### 1. Generate a Private Key and CSR

Use OpenSSL to generate a private key and a Certificate Signing Request:

```bash
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=your-company-name"
```

> [!IMPORTANT]
> Keep your private key (`client.key`) secure. Never share it with anyone, including Payout. Only the CSR is uploaded.

### 2. Upload the CSR in the Merchant Portal

1. Log in to the Merchant Portal ([Sandbox](https://sandbox.payout.one) or [Production](https://app.payout.one)).
2. Navigate to **Developers** → **API Keys** → select your API key → **Edit**.
3. Go to the **mTLS** tab.
4. Upload your `client.csr` file.
5. Click **Sign CSR**.
6. Download the signed certificate (`client-cert.pem`).

Once the CSR is signed, the certificate fingerprint is automatically linked to your API key. All subsequent calls to `/api/v2` must include this certificate.

### 3. Authorize

Obtain a Bearer token using the standard authorization endpoint:

```bash
curl --location --request POST 'https://app.payout.one/api/v1/authorize' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data-raw '{
  "client_id": "<your_client_id>",
  "client_secret": "<your_client_secret>"
}'
```

Response:

```json
{
  "token": "SFMyNTY...",
  "valid_for": 6000
}
```

### 4. Make API Calls with Your Client Certificate

Include the signed certificate and private key in every request to `/api/v2` endpoints:

```bash
curl --cert client-cert.pem --key client.key \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer <your_token>' \
  --header 'Accept: application/json' \
  https://app.payout.one/api/v2/withdrawals
```

## API v2 Endpoints

### Create Withdrawal

```
POST /api/v2/withdrawals
```

```bash
curl --cert client-cert.pem --key client.key \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer <your_token>' \
  --header 'Accept: application/json' \
  --header 'Idempotency-Key: <unique_key>' \
  --data-raw '{
    "amount": 300,
    "currency": "EUR",
    "external_id": "<merchant_id>",
    "iban": "<iban>",
    "customer": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com"
    },
    "signature": "<signature>",
    "nonce": "<nonce>",
    "statement_descriptor": "Withdrawal description"
  }' \
  https://app.payout.one/api/v2/withdrawals
```

> [!NOTE]
> Amount is in cents (EUR), so 3 EUR is 300. The same applies for other currencies — for example, 300 CZK is 30000.

**Signature** is generated from the following pattern:

```
amount|currency|external_id|iban|nonce|client_secret
```

This string is hashed with SHA256 and encoded in lowercase hexadecimal form.

### List Withdrawals

```
GET /api/v2/withdrawals
```

Optional query parameters: `limit`, `offset`, `order` (ASC/DESC).

### Get Withdrawal

```
GET /api/v2/withdrawals/:id
```

### Cancel Withdrawal

```
POST /api/v2/withdrawals/:id/cancel
```

### Check Cancel Allowed

```
POST /api/v2/withdrawals/:id/cancel_allowed
```

## Error Responses

| HTTP Status | Meaning |
|---|---|
| 403 Forbidden | Client certificate is missing, invalid, or does not match the API key. |
| 401 Unauthorized | Bearer token is missing or expired. |

## Security Architecture

The mTLS implementation uses a two-layer verification model:

1. **TLS Layer (Nginx Ingress)** — During the TLS handshake, the server requests a client certificate. Nginx verifies that:
   - The certificate is signed by the Payout Certificate Authority.
   - The client possesses the private key corresponding to the certificate.

2. **Application Layer (Payout API)** — After the TLS handshake, the application verifies that:
   - The SHA-256 fingerprint of the presented certificate matches the fingerprint registered to the API key.

This dual verification ensures that even if a certificate signed by the same CA is compromised, it cannot be used with a different API key.

## Certificate Management

- Each API key can have **one active certificate** at a time.
- To rotate a certificate, generate a new CSR, upload it via the Merchant Portal, and start using the new certificate. The previous certificate will be invalidated.
- Certificates are signed by the Payout CA with a defined validity period.

## FAQ

**Can I use the same certificate for multiple API keys?**
No. Each API key must have its own unique certificate.

**What happens if I call `/api/v2` without a certificate?**
You will receive a `403 Forbidden` response.

**What happens if I call `/api/v2` with a certificate that does not match my API key?**
You will receive a `403 Forbidden` response.

**Can I still use `/api/v1` endpoints?**
Yes. The `/api/v1` endpoints remain available and do not require a client certificate.

**What certificate format is required?**
The CSR must be in PEM format (the standard output of `openssl req`). The signed certificate returned by Payout is also in PEM format.

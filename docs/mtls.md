# M2M API — mTLS + QSEAL

Payout API v2 endpoints for M2M (machine-to-machine) payment initiation are secured with two qualified certificates issued by a Qualified Trust Service Provider (QTSP) under the EU eIDAS regulation:

- **QWAC** (Qualified Website Authentication Certificate) — establishes a mutually authenticated TLS connection (mTLS).
- **QSEAL** (Qualified Electronic Seal Certificate) — digitally signs each payment instruction (detached JWS).

This model is aligned with the Berlin Group NextGenPSD2 framework and is required by Article 17 RTS to SCA for the corporate payment process exemption.

The mTLS certificate-management endpoints under `/api/v1/mtls/certificates` are the **shared infrastructure** for any server-to-server Payout API that requires a TLS client certificate. Today that means PSD2 payment initiation (this page); upcoming products such as Verification of Payee will reuse the same import/approval flow with a less strict certificate profile.

## Endpoints

| Environment | mTLS host |
|---|---|
| **Sandbox** | `https://api-mtls-sandbox.payout.one` |
| **Production** | `https://api-mtls.payout.one` |

The token-issuing endpoint and certificate import endpoints remain on the standard hosts (`sandbox.payout.one` / `app.payout.one`).

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/authorize` | Obtain Bearer token from `client_id` + `client_secret` |
| `POST` | `/api/v1/mtls/certificates` | Import a QWAC or QSEAL certificate |
| `GET` | `/api/v1/mtls/certificates` | List your imported certificates |
| `GET` | `/api/v1/mtls/certificates/:thumbprint/status` | Check certificate approval status |
| `DELETE` | `/api/v1/mtls/certificates/:thumbprint` | Remove a certificate |
| `POST` | `/api/v2/withdrawals` | **mTLS + QSEAL** — create a withdrawal |
| `GET` | `/api/v2/withdrawals` | **mTLS** — list withdrawals |
| `GET` | `/api/v2/withdrawals/:id` | **mTLS** — retrieve withdrawal |
| `POST` | `/api/v2/withdrawals/:id/cancel` | **mTLS + QSEAL** — cancel a withdrawal (only when status is `pending`) |
| `POST` | `/api/v2/withdrawals/:id/cancel_allowed` | **mTLS** — check whether cancel is allowed |

## Setup

### 1. Obtain certificates from a QTSP

You must obtain both a QWAC and a QSEAL certificate from any EU-recognised Qualified Trust Service Provider listed in the [EU Trusted List](https://ec.europa.eu/tools/lotl/eu-lotl.xml). Examples: I.CA, Disig, D-Trust, Buypass, GlobalSign Qualified, A-Trust, Certinomis.

Requirements:

- **QWAC** — issued for TLS client authentication, key usage `digitalSignature` + `keyEncipherment`.
- **QSEAL** — issued for electronic seals, key usage `nonRepudiation`.
- Both must contain your organisation identifier (IČO / LEI) in the certificate subject (`organizationIdentifier` attribute).
- Minimum key size: RSA 2048 or ECDSA P-256.

Generate the private keys yourself and send only the CSR to the QTSP. **The private keys must never leave your infrastructure.**

### 2. Obtain a Bearer token

```bash
curl -X POST https://app.payout.one/api/v1/authorize \
  -H "Content-Type: application/json" \
  -d '{"client_id":"<CLIENT_ID>","client_secret":"<CLIENT_SECRET>"}'
```

Response:

```json
{ "token": "...", "valid_for": 6000 }
```

### 3. Import your certificates

Upload the PEM-encoded QWAC and QSEAL certificates (public part only, not the private keys):

```bash
curl -X POST https://app.payout.one/api/v1/mtls/certificates \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "qwac",
    "pem": "-----BEGIN CERTIFICATE-----\n..."
  }'
```

Repeat for the QSEAL certificate with `"type": "qseal"`.

Response (initial state `pending`):

```json
{
  "type": "qwac",
  "thumbprint": "49165a9f...",
  "status": "pending",
  "issuer_dn": "CN=...,O=...",
  "subject_dn": "C=SK,...,organizationIdentifier=PSDSK-NBS-50487787,CN=...",
  "subject_org_id": "PSDSK-NBS-50487787",
  "valid_from": "2025-06-09T06:23:06Z",
  "valid_until": "2026-06-09T06:23:06Z"
}
```

### 4. Wait for manual approval

Payout manually verifies that the imported certificates match the contractual data of your account. You can check the status at any time:

```bash
curl https://app.payout.one/api/v1/mtls/certificates/<thumbprint>/status \
  -H "Authorization: Bearer <TOKEN>"
```

After approval the status changes to `approved` and the certificate becomes usable for M2M operations.

### 5. Call the M2M API

Once both certificates are `approved`, you can call the v2 endpoints on the dedicated mTLS host using your QWAC during the TLS handshake.

## Signing payment instructions with QSEAL

Each request that creates or modifies a payment (`POST /api/v2/withdrawals`, `POST /api/v2/withdrawals/:id/cancel`, etc.) must be signed with a detached JWS produced by the private key of your QSEAL certificate.

### Required headers

| Header | Value |
|---|---|
| `Authorization` | `Bearer <TOKEN>` |
| `Content-Type` | `application/json` |
| `Digest` | `SHA-256=<base64(sha256(body))>` |
| `X-JWS-Signature` | `<protected-header>..<signature>` (detached JWS) |

### JWS protected header

The protected header is a base64url-encoded JSON object:

```json
{
  "alg": "PS256",
  "typ": "JOSE+JSON",
  "x5t#S256": "<sha256 thumbprint of QSEAL cert, lowercase hex>",
  "crit": ["sigT", "sigD"],
  "sigT": "2026-05-15T10:00:00Z",
  "sigD": {
    "mId": "http://uri.etsi.org/19182/HttpHeaders",
    "pars": ["digest"]
  }
}
```

The signed payload is the value of the `Digest` header (not the body itself). Accepted algorithms: `PS256`, `RS256`, `ES256`.

### Signing flow (pseudocode)

```
body          = '{"amount":"100","currency":"EUR",...}'
digest_b64    = base64( sha256(body) )
digest_header = "SHA-256=" + digest_b64

protected_b64 = base64url( JSON.stringify(protected_header) )
payload_b64   = base64url( digest_header )
signing_input = protected_b64 + "." + payload_b64

signature_b64 = base64url( sign(signing_input, qseal_private_key, "PS256") )

x_jws_signature = protected_b64 + ".." + signature_b64
```

### Server-side verification

Payout verifies, for every QSEAL-signed request:

1. The `Digest` header matches the recomputed SHA-256 of the body.
2. The protected header carries an `x5t#S256` matching an `approved` QSEAL certificate registered to your account.
3. The certificate is within its validity period.
4. `sigT` is within ±5 minutes of server time (replay protection).
5. The JWS signature is valid against the QSEAL public key.

Any failure results in HTTP `403 Forbidden`.

## Example: full request

```http
POST /api/v2/withdrawals HTTP/1.1
Host: api-mtls.payout.one
Authorization: Bearer <TOKEN>
Content-Type: application/json
Digest: SHA-256=Lk8nE3bXPzZl0vKqK4kxA7FpQs4sLm1L3xVpNlRb6w0=
X-JWS-Signature: eyJhbGciOiJQUzI1NiIsInR5cCI6IkpPU0UrSlNPTiIsIng1dCNTMjU2I...

{
  "amount": "10000",
  "currency": "EUR",
  "external_id": "merchant-tx-2026-05-15-001",
  "iban": "SK0511000000002600000054",
  "customer": {
    "first_name": "Anna",
    "last_name": "Nová",
    "email": "anna.nova@example.com"
  },
  "statement_descriptor": "Platba 2026/05",
  "nonce": "5b6e9c1a-f4a2-4c11-9e56-2f93e1c7a3d0"
}
```

> [!NOTE]
> When the request is signed with QSEAL, the legacy HMAC `signature` field used in `/api/v1/withdrawals` is **not required** in v2. QSEAL provides equivalent integrity and authenticity for the entire payload.

## Certificate lifecycle

### Renewal

When your certificate approaches expiry, obtain a new one from the QTSP and import it via `POST /api/v1/mtls/certificates`. The new certificate is approved separately and runs in parallel with the previous one until that one expires — no downtime.

### Revocation

You can remove your own certificate at any time:

```bash
curl -X DELETE https://app.payout.one/api/v1/mtls/certificates/<thumbprint> \
  -H "Authorization: Bearer <TOKEN>"
```

Payout may also revoke a certificate if it has been compromised or if the contractual relationship ends. In that case, you will be notified by email and via webhook (`mtls_certificate.revoked`).

### Compromise

If you suspect your private key has been compromised:

1. Revoke the certificate at the QTSP that issued it.
2. Remove it from Payout (`DELETE`).
3. Notify Payout at `security@payout.one`.
4. Generate a new key pair and obtain a fresh certificate.
5. Import the new certificate and wait for re-approval.

## HTTP error codes

| Code | Meaning |
|---|---|
| `401 Unauthorized` | Missing or invalid Bearer token |
| `403 Forbidden` | mTLS failure, QSEAL signature failure, or business rule rejection (insufficient balance, IBAN blocked, etc.) |
| `404 Not Found` | Resource (certificate, withdrawal) not found or not owned by your account |
| `409 Conflict` | Certificate with the same thumbprint already imported |
| `422 Unprocessable Entity` | Validation error (malformed PEM, invalid IBAN, missing field, etc.) |
| TLS handshake refused | Client certificate missing, expired, revoked, or not issued by a trusted QTSP |

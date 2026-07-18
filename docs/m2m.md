# M2M Withdrawals — mTLS + QSEAL

The **M2M Withdrawals** API is Payout API v2's server-to-server interface for initiating, retrieving and cancelling withdrawals (outbound transfers from your Payout balance to a customer's IBAN). It is secured by two qualified certificates issued by a Qualified Trust Service Provider (QTSP) under the EU eIDAS regulation:

- **QWAC** (Qualified Website Authentication Certificate) — establishes a mutually authenticated TLS connection (mTLS).
- **QSEAL** (Qualified Electronic Seal Certificate) — digitally signs each payment instruction (detached JWS).

> Certificate import, approval and lifecycle are documented separately in [**Certificates**](./certificates.md). This page covers only what is **withdrawal-specific**: hosts, endpoints, QSEAL signing, and the M2M-specific error behaviour.

## Endpoints

| Environment | mTLS host |
|---|---|
| **Sandbox** | `https://api-mtls-sandbox.payout.one` |
| **Production** | `https://api-mtls.payout.one` |

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v2/withdrawals` | **mTLS + QSEAL** — create a withdrawal |
| `GET`  | `/api/v2/withdrawals` | **mTLS** — list withdrawals |
| `GET`  | `/api/v2/withdrawals/:id` | **mTLS** — retrieve withdrawal |
| `POST` | `/api/v2/withdrawals/:id/cancel` | **mTLS + QSEAL** — cancel a withdrawal (only when status is `pending`) |
| `POST` | `/api/v2/withdrawals/:id/cancel_allowed` | **mTLS** — check whether cancel is allowed |

## Prerequisites

Before you can call any v2 withdrawal endpoint you need an `approved` **QWAC** *and* an `approved` **QSEAL** certificate registered to your account. Both must be issued by a supported QTSP on the [EU Trusted List](https://ec.europa.eu/tools/lotl/eu-lotl.xml) — currently **I.CA** and **Disig** (for a certificate from another EUTL QTSP, contact [tech@payout.one](mailto:tech@payout.one)). Standard eIDAS qualified certificates are sufficient — no PSD2-specific extensions are required (see [Certificates § Certificate profiles](./certificates.md#certificate-profiles)).

Full setup is in [Certificates § Setup](./certificates.md#setup). In summary:

1. Obtain QWAC + QSEAL from a QTSP (standard eIDAS qualified certificates, no PSD2 extensions required).
2. Import both via `POST /api/v1/mtls/certificates` against the standard host (`sandbox.payout.one` / `app.payout.one`).
3. Wait for manual approval by Payout.
4. Call the v2 endpoints on the mTLS host, presenting the QWAC during the TLS handshake.

## Signing payment instructions with QSEAL

Every request that **creates or modifies** a payment (`POST /api/v2/withdrawals`, `POST /api/v2/withdrawals/:id/cancel`) must be signed with a detached JWS produced by the private key of your QSEAL certificate. Read-only requests (`GET …`, `cancel_allowed`) are authenticated by mTLS alone.

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

## HTTP error codes

Generic cert/transport errors (401 token, 403 cert not approved, 409 cert thumbprint conflict, TLS handshake refused) are described in [Certificates § HTTP error codes](./certificates.md#http-error-codes). The list below is **withdrawal-specific**:

| Code | Meaning |
|---|---|
| `403 Forbidden` | QSEAL signature failure, **or** business rule rejection (insufficient balance, IBAN blocked, payee on sanctions list, etc.) |
| `404 Not Found` | Withdrawal not found, or not owned by your account |
| `422 Unprocessable Entity` | Validation error on the withdrawal payload (invalid IBAN, missing `customer.first_name`, currency not enabled, etc.) |
| `409 Conflict` | Withdrawal with the same `external_id` already exists |

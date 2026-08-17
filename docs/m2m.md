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
  "nonce": "5b6e9c1a-f4a2-4c11-9e56-2f93e1c7a3d0",
  "require_vop": true,
  "additional_attribute": "Invoice 2026/05/017"
}
```

> [!NOTE]
> When the request is signed with QSEAL, the legacy HMAC `signature` field used in `/api/v1/withdrawals` is **not required** in v2. QSEAL provides equivalent integrity and authenticity for the entire payload.

## Verification of Payee (VoP)

You can ask Payout to run a **Verification of Payee** check as part of a withdrawal — confirming that the name you provided matches the account holder that the beneficiary bank holds for the IBAN. There is no separate VoP endpoint; you opt in per withdrawal with the optional `require_vop` field in the create request.

| Field | Type | Required | Description |
|---|---|---|---|
| `require_vop` | boolean | no | Default `false`. When `true`, Payout runs a VoP check on the withdrawal's `iban` and `customer` name and delivers the result via a webhook (see below). |
| `additional_attribute` | string | no | Free-text metadata echoed back in the VoP webhook (e.g. internal reference, invoice number). |

The check compares the name in `customer` (`first_name` + `last_name`) — or the organisation name for a legal entity — against the account holder registered for the withdrawal's `iban`. It does **not** block the withdrawal; it runs alongside and reports its result asynchronously.

> [!NOTE]
> VoP returns a **match outcome**, not an authoritative truth. A `CLOSE_MATCH` does not automatically mean the payment is safe — surface the returned `real_name` to your operator and let them confirm or cancel.

### VoP webhook

As soon as the VoP result is known, Payout sends a **dedicated webhook** of type **`withdrawal.vop_result`** to your configured webhook URL. It uses the standard webhook envelope; the `data` object carries the VoP outcome plus the identifiers you need to match it to the originating withdrawal:

```json
{
  "type": "withdrawal.vop_result",
  "object": "webhook",
  "data": {
    "match_result": "CLOSE_MATCH",
    "real_name": "Anna Nová-Kováčová",
    "reference_id": "f1c8d4a3-2e90-4a52-9b13-7c8a1d4e5b21",
    "timestamp": "2026-05-20T10:14:33Z",
    "additional_attribute": "Invoice 2026/05/017",
    "withdrawal_id": 90412,
    "external_id": "merchant-tx-2026-05-15-001"
  },
  "nonce": "UzhER2lFOFZCNkNQVmNuNQ",
  "signature": "b95494dd09183b7cbca40f356d7s4f567sdf765sdf79e1f4a95e936",
}
```

`data` fields:

| Field | Type | Description |
|---|---|---|
| `match_result` | enum | One of `MATCH`, `CLOSE_MATCH`, `NO_MATCH`, `CANNOT_VERIFY`. |
| `real_name` | string | Present only when `match_result == CLOSE_MATCH` — the name the beneficiary bank holds, returned so you can show it to the operator for confirmation. |
| `reference_id` | UUID | Server-generated ID for audit traceability — quote this when raising support tickets. |
| `timestamp` | ISO 8601 | UTC datetime when the check was processed. |
| `additional_attribute` | string | Echo of the `additional_attribute` from the withdrawal request (if provided). |
| `withdrawal_id` | integer | Payout ID of the withdrawal this VoP check belongs to. |
| `external_id` | string | Your `external_id` from the withdrawal request — for client-side matching. |

### Match outcomes

| Outcome | Meaning | Recommended handling |
|---|---|---|
| `MATCH` | Full correspondence between the submitted name and the beneficiary bank's records. | Proceed with the payment. |
| `CLOSE_MATCH` | Partial correspondence (typos, missing diacritics, suffix mismatch). `real_name` is returned. | Show `real_name` to the operator; let them confirm or cancel. |
| `NO_MATCH` | No correspondence — the name does not belong to the IBAN. | Block the payment; warn the operator. |
| `CANNOT_VERIFY` | The check could not be completed (beneficiary bank unreachable, IBAN unknown to it, or the bank has opted out of VoP). | Inconclusive — your risk policy decides whether to proceed. |

VoP only tells you whether the name on the account matches the IBAN. It is **not** a substitute for AML screening, sanctions list checks, or any other due-diligence step you are independently required to perform on a payee.

## HTTP error codes

Generic cert/transport errors (401 token, 403 cert not approved, 409 cert thumbprint conflict, TLS handshake refused) are described in [Certificates § HTTP error codes](./certificates.md#http-error-codes). The list below is **withdrawal-specific**:

| Code | Meaning |
|---|---|
| `403 Forbidden` | QSEAL signature failure, **or** business rule rejection (insufficient balance, IBAN blocked, payee on sanctions list, etc.) |
| `404 Not Found` | Withdrawal not found, or not owned by your account |
| `422 Unprocessable Entity` | Validation error on the withdrawal payload (invalid IBAN, missing `customer.first_name`, currency not enabled, etc.) |
| `409 Conflict` | Withdrawal with the same `external_id` already exists |

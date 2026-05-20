# Verification of Payee (VoP)

The **Verification of Payee** API lets you check whether an IBAN belongs to a given payee — natural person or legal entity — **before** you send them money. You submit the IBAN and the name (or organisation identifier) you have on file; we return a match outcome that your application can act on.

> [!NOTE]
> VoP returns a **match outcome**, not an authoritative truth. A `CLOSE_MATCH` does not automatically mean the payment is safe — your application is expected to surface the returned `real_name` to the operator (AP clerk, end-user, etc.) and let them confirm or cancel.

## Endpoints

| Environment | mTLS host |
|---|---|
| **Sandbox** | `https://api-mtls-sandbox.payout.one` |
| **Production** | `https://api-mtls.payout.one` |

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v2/payee_verification` | **mTLS** — perform a VoP check |

The certificate import endpoints (`/api/v1/mtls/certificates`) and the token-issuing endpoint (`/api/v1/authorize`) remain on the standard hosts (`sandbox.payout.one` / `app.payout.one`).

## Authentication

VoP is authenticated by:

- A **Bearer token** issued from your `client_id` + `client_secret` (`POST /api/v1/authorize`).
- An **mTLS handshake** with a [Qualified Website Authentication Certificate (QWAC)](./certificates.md) issued to your legal entity by an EU Qualified Trust Service Provider (QTSP).

Any legal entity can obtain a QWAC from a QTSP — there is no PSP licence requirement. See [Certificates § Setup](./certificates.md#setup) for the import + approval flow.

## Request

### Headers

| Header | Value |
|---|---|
| `Authorization` | `Bearer <TOKEN>` |
| `Content-Type` | `application/json` |
| `Idempotency-Key` | UUID v4 — required, prevents duplicate processing on retry |

### Body

```json
{
  "iban": "SK0511000000002600000054",
  "account_holder_name": "Anna Nová",
  "additional_attribute": "Invoice 2026/05/017"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `iban` | string | yes | IBAN to verify. |
| `account_holder_name` | string | conditional | Name of the natural person or legal entity. **Either** `account_holder_name` **or** `organisation_identification` must be present. |
| `organisation_identification` | object | conditional | Legal-entity identifier — see below. Alternative to `account_holder_name`. |
| `additional_attribute` | string | no | Free-text metadata that will be echoed back in the response (e.g. internal reference, payment context). |

### `organisation_identification` object

```json
{
  "organisation_identification": {
    "lei": "529900T8BM49AURSDO55"
  }
}
```

Provide exactly one of:

| Field | Type | Description |
|---|---|---|
| `lei` | string | Legal Entity Identifier per ISO 17442. |
| `bic` | string | Business Identifier Code per ISO 9362. |
| `other` | object | Custom scheme — see below. |

`other` object:

| Field | Required | Description |
|---|---|---|
| `identification` | yes | The identifier value (string). |
| `scheme_name_code` | conditional | Externally-coded scheme name from ISO 20022 `ExternalOrganisationIdentification1Code` — e.g. `COID`, `TXID`, `BANK`. |
| `scheme_name_proprietary` | conditional | Proprietary scheme name (string). Use this **or** `scheme_name_code`, not both. |
| `issuer` | no | Issuer of the identification. |

## Response

### `200 OK`

```json
{
  "match_result": "CLOSE_MATCH",
  "real_name": "Anna Nová-Kováčová",
  "reference_id": "f1c8d4a3-2e90-4a52-9b13-7c8a1d4e5b21",
  "timestamp": "2026-05-20T10:14:33Z",
  "additional_attribute": "Invoice 2026/05/017"
}
```

| Field | Type | Description |
|---|---|---|
| `match_result` | enum | One of `MATCH`, `CLOSE_MATCH`, `NO_MATCH`, `CANNOT_VERIFY`. |
| `real_name` | string | Present only when `match_result == CLOSE_MATCH`. The name the account holder's bank holds for the account, returned so your application can show it to the operator for confirmation. |
| `reference_id` | UUID | Server-generated ID for audit traceability — quote this when raising support tickets. |
| `timestamp` | ISO 8601 | UTC datetime when the check was processed. |
| `additional_attribute` | string | Echo of the request `additional_attribute` (if provided). |

### Match outcomes

| Outcome | Meaning | Recommended UX |
|---|---|---|
| `MATCH` | Full correspondence between the submitted name/ID and the records held by the account holder's bank. | Proceed with the payment. |
| `CLOSE_MATCH` | Partial correspondence (typos, missing diacritics, suffix mismatch). `real_name` is returned. | Show `real_name` to the operator; let them confirm or cancel. |
| `NO_MATCH` | No correspondence — the name does not belong to the IBAN. | Block the payment; warn the operator. |
| `CANNOT_VERIFY` | The check could not be completed (e.g. the account holder's bank is unreachable, the IBAN is unknown to it, or the bank has opted out of VoP). | Treat as inconclusive — your risk policy decides whether to proceed. |

### Error responses

Errors follow [RFC 9457 — Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc9457) (`Content-Type: application/problem+json`).

| Code | Meaning |
|---|---|
| `400 Bad Request` | Malformed JSON, missing both `account_holder_name` and `organisation_identification`, invalid `Idempotency-Key`, etc. |
| `401 Unauthorized` | Missing or invalid Bearer token. |
| `403 Forbidden` | mTLS handshake failed, certificate not `approved`, or your account is not entitled to use VoP. |
| `409 Conflict` | The same `Idempotency-Key` was used previously with a **different** request body. Use a fresh UUID. |
| `422 Unprocessable Entity` | Validation error (e.g. invalid `lei` / `bic`). |

## Idempotency

Every request **must** carry a unique `Idempotency-Key` (UUID v4). When the same key is replayed with the **same** body, Payout returns the original response. Replays with a different body return `409 Conflict`.

This makes it safe to retry on network failures (timeouts, transient 5xx) without risk of duplicate processing.

## Example: full request

```http
POST /api/v2/payee_verification HTTP/1.1
Host: api-mtls.payout.one
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
Idempotency-Key: 7c5f5e2a-2a4b-4cb6-8e88-44d2bf8c2c9c

{
  "iban": "SK0511000000002600000054",
  "account_holder_name": "Anna Nová",
  "additional_attribute": "Invoice 2026/05/017"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "match_result": "CLOSE_MATCH",
  "real_name": "Anna Nová-Kováčová",
  "reference_id": "f1c8d4a3-2e90-4a52-9b13-7c8a1d4e5b21",
  "timestamp": "2026-05-20T10:14:33Z",
  "additional_attribute": "Invoice 2026/05/017"
}
```

## Scope

VoP only tells you whether the name on the account matches the IBAN. It is **not** a substitute for AML screening, sanctions list checks, or any other due-diligence step you are independently required to perform on a payee.

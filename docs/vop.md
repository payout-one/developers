# Verification of Payee (VoP)

The **Verification of Payee** API lets you check whether an IBAN belongs to a given account holder **before** you initiate a payment. It is implemented in line with the [EPC Verification of Payee Scheme Rulebook](https://www.europeanpaymentscouncil.eu/) (effective October 2025 under the EU Instant Payments Regulation).

> [!NOTE]
> VoP returns a **match outcome**, not an authoritative truth. The responding PSP performs a name comparison against its own records; a `CLOSE_MATCH` does not mean the payment is safe — your application is expected to surface the returned `real_name` to the end-user and let them confirm.

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

VoP uses the same [mTLS client-certificate](./certificates.md) infrastructure as [M2M Withdrawals](./m2m.md) — but with a **lower certificate profile**, because VoP is a read-only query rather than a payment instruction:

| Requirement | M2M Withdrawals | VoP |
|---|---|---|
| Bearer token | required | required |
| mTLS (client cert) | required | required |
| Certificate must be eIDAS-qualified (QWAC) | yes | yes |
| QWAC must carry a PSD2 role attribute (`PSDxx-…`) | **yes** — PSP licence required | **no** — any legal entity may obtain a plain eIDAS QWAC |
| QSEAL detached JWS signature on the request | required (`X-JWS-Signature` header) | **not required** |

A single QWAC may serve both products if your organisation holds a PSD2 role; otherwise a plain eIDAS QWAC is sufficient for VoP. The import + approval flow is identical for both — see [Certificates § Setup](./certificates.md#setup).

## Request

### Headers

| Header | Value |
|---|---|
| `Authorization` | `Bearer <TOKEN>` |
| `Content-Type` | `application/json` |
| `Idempotency-Key` | UUID v4 — required, prevents double-billing on retry |

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
| `iban` | string | yes | IBAN to verify. No format validation — pass it as you have it. |
| `account_holder_name` | string | conditional | Name of the natural person or legal entity. **Either** `account_holder_name` **or** `organisation_identification` must be present. |
| `organisation_identification` | object | conditional | Legal-entity identifier — see below. Alternative to `account_holder_name`. |
| `additional_attribute` | string | no | Free-text metadata returned in the response (e.g. internal reference, payment context). Max 140 chars. |
| `responding_psp_bic` | string | no | 8 or 11-char ISO 9362 BIC of the responding PSP. Provide only if you already know it; otherwise Payout will route the lookup based on the IBAN. |

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
| `lei` | string | Legal Entity Identifier per ISO 17442 (20 chars). |
| `bic` | string | Business Identifier Code per ISO 9362 (8 or 11 chars). |
| `other` | object | Custom scheme — see below. |

`other` object:

| Field | Required | Description |
|---|---|---|
| `identification` | yes | The identifier value (string). |
| `scheme_name_code` | conditional | Externally-coded scheme name from [ISO 20022 ExternalOrganisationIdentification1Code](https://www.iso20022.org/) — e.g. `COID`, `TXID`, `BANK`. |
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
| `real_name` | string | Present only when `match_result == CLOSE_MATCH`. The name the responding PSP holds for the account, returned so your application can show it to the end-user for confirmation. |
| `reference_id` | UUID | Server-generated ID for audit traceability — quote this when raising support tickets. |
| `timestamp` | ISO 8601 | UTC datetime when the responding PSP processed the check. |
| `additional_attribute` | string | Echo of the request `additional_attribute` (if provided). |

### Match outcomes

| Outcome | Meaning | Recommended UX |
|---|---|---|
| `MATCH` | Full correspondence between the submitted name/ID and the PSP's records. | Proceed with the payment. |
| `CLOSE_MATCH` | Partial correspondence (typos, missing diacritics, suffix mismatch). `real_name` is returned. | Show `real_name` to the user, let them confirm or cancel. |
| `NO_MATCH` | No correspondence — the name does not belong to the IBAN. | Block the payment, warn the user. |
| `CANNOT_VERIFY` | The responding PSP could not complete the check (PSP unreachable, IBAN unknown, opt-out). | Treat as inconclusive — your risk-policy decides whether to proceed. |

### Error responses

Errors follow [RFC 9457 — Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc9457) (`Content-Type: application/problem+json`).

| Code | Meaning |
|---|---|
| `400 Bad Request` | Malformed JSON, missing both `account_holder_name` and `organisation_identification`, invalid `Idempotency-Key`, etc. |
| `401 Unauthorized` | Missing or invalid Bearer token. |
| `403 Forbidden` | mTLS handshake failed, certificate not `approved`, or your account is not entitled to use VoP. |
| `409 Conflict` | The same `Idempotency-Key` was used previously with a **different** request body. Use a fresh UUID. |
| `422 Unprocessable Entity` | Validation error (e.g. `lei` failed checksum, `bic` wrong length). |
| `429 Too Many Requests` | Rate limit exceeded — `Retry-After` header included. |
| `503 Service Unavailable` | Downstream responding PSP unreachable; safe to retry with the same `Idempotency-Key`. |

## Idempotency

Every request **must** carry a unique `Idempotency-Key` (UUID v4). Payout stores the response for 24 hours and returns the **same** payload (status code + body) when the same key is replayed with the **same** body. Replays with a different body return `409 Conflict`.

This means it is **safe to retry** on network failures (timeouts, 5xx) without risk of double-billing or duplicate audit entries.

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

## Rate limits

- **Sandbox:** 60 req/min per account.
- **Production:** 600 req/min per account by default. Higher limits are available — contact `integration@payout.one`.

Exceeding the limit returns `429 Too Many Requests` with a `Retry-After` header (seconds).

## Data retention & audit

- Every VoP request is logged with its `reference_id`, `Idempotency-Key`, requesting account, the responding PSP's BIC, and the `match_result`. Logs are retained for **5 years** in line with AML record-keeping requirements.
- The full submitted payload (IBAN + name) is **not** retained beyond 24 hours — only the cryptographic fingerprint required to enforce idempotency.
- You can retrieve audit records via the support portal by quoting the `reference_id`.

## Operational notes

- VoP is **not** a substitute for SCA, AML screening, or sanctions list checks — it only verifies that the name on the account matches the IBAN.
- Some responding PSPs (especially smaller institutions) may consistently return `CANNOT_VERIFY` while they are still onboarding to the EPC VoP scheme. Track per-PSP coverage with the `responding_psp_bic` field in the response.
- For high-volume bulk verification (payroll, supplier onboarding), batch requests are on the roadmap — contact `integration@payout.one` if you need this before GA.

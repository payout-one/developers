# mTLS client certificates

The Payout server-to-server APIs are authenticated with an **mTLS client certificate** that you obtain from a Qualified Trust Service Provider (QTSP) and import into your Payout account. The same certificate infrastructure is reused by every server-to-server product:

- [**M2M Withdrawals**](./m2m.md) — Payout API v2 withdrawal initiation, including optional [Verification of Payee](./m2m.md#verification-of-payee-vop). Requires a QWAC for the mTLS connection **plus** a QSEAL for detached payment-instruction signatures.
- *(more products to come — same import flow.)*

If you already imported a certificate for one product, you can reuse it for the other(s) as long as it satisfies their respective profile requirements.

## Certificate profiles

| Profile | What it is | Required for |
|---|---|---|
| **QWAC** (Qualified Website Authentication Certificate) | Establishes the mTLS connection. Issued by a QTSP, listed in the EU Trusted List. | All server-to-server APIs |
| **QSEAL** (Qualified Electronic Seal Certificate) | Signs payment instructions (detached JWS). Issued by a QTSP. | M2M Withdrawals only |

A standard eIDAS QWAC and QSEAL are sufficient — **no PSD2-specific extensions** (QcStatement-PSD2 per ETSI TS 119 495, PSP role attributes such as `PSP_AS`/`PSP_PI`/`PSP_AI`/`PSP_IC`) are required. Those are issued only to licensed payment service providers; M2M clients are typically merchants and other B2B entities and obtain plain qualified certificates from a supported EU Trusted List QTSP (currently I.CA and Disig; for another issuer, contact [tech@payout.one](mailto:tech@payout.one)).

Common requirements for all profiles:

- Issued by a QTSP listed in the [EU Trusted List](https://ec.europa.eu/tools/lotl/eu-lotl.xml). **Currently supported issuers: I.CA (První certifikační autorita) and Disig.** To use a certificate from another EU Trusted List QTSP, contact [tech@payout.one](mailto:tech@payout.one) and we will add its CA to our trust store.
- Contains your organisation identifier (IČO / LEI / VAT) in the `organizationIdentifier` subject attribute.
- Key usage matches the certificate's role:
  - QWAC — `digitalSignature` + `keyEncipherment`
  - QSEAL — `nonRepudiation`
- Minimum key size: RSA 2048 or ECDSA P-256.

Generate the private keys yourself and send only the CSR to the QTSP. **The private keys must never leave your infrastructure.**

## Endpoints

Certificate management lives on the standard hosts (not the mTLS hosts), because import happens **before** mTLS is usable:

| Environment | Host |
|---|---|
| **Sandbox** | `https://sandbox.payout.one` |
| **Production** | `https://app.payout.one` |

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/authorize` | Obtain Bearer token from `client_id` + `client_secret` |
| `POST` | `/api/v1/mtls/certificates` | Import a QWAC or QSEAL certificate |
| `GET`  | `/api/v1/mtls/certificates` | List your imported certificates |
| `GET`  | `/api/v1/mtls/certificates/:thumbprint/status` | Check certificate approval status |
| `DELETE` | `/api/v1/mtls/certificates/:thumbprint` | Remove a certificate |

## Setup

### 1. Obtain certificate(s) from a QTSP

See the [Certificate profiles](#certificate-profiles) table above for which profiles you need. Then submit a CSR to the QTSP of your choice.

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

### 3. Import your certificate(s)

Upload the PEM-encoded certificate (public part only, never the private key):

```bash
curl -X POST https://app.payout.one/api/v1/mtls/certificates \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "qwac",
    "pem": "-----BEGIN CERTIFICATE-----\n..."
  }'
```

For M2M Withdrawals, repeat for the QSEAL certificate with `"type": "qseal"`.

Response (initial state `pending`):

```json
{
  "type": "qwac",
  "thumbprint": "49165a9f...",
  "status": "pending",
  "issuer_dn": "CN=...,O=...",
  "subject_dn": "C=SK,...,organizationIdentifier=NTRSK-12345678,CN=...",
  "subject_org_id": "NTRSK-12345678",
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

After approval the status changes to `approved` and the certificate becomes usable.

### 5. Start calling the API

Once the certificate is `approved`, present it during the TLS handshake against the relevant mTLS host:

| API | mTLS host (sandbox) | mTLS host (production) |
|---|---|---|
| [M2M Withdrawals](./m2m.md) | `api-mtls-sandbox.payout.one` | `api-mtls.payout.one` |

## Lifecycle

### Renewal

When your certificate approaches expiry, obtain a new one from the QTSP and import it via `POST /api/v1/mtls/certificates`. The new certificate is approved separately and runs in parallel with the previous one until that one expires — **no downtime**.

### Revocation (by you)

You can remove your own certificate at any time:

```bash
curl -X DELETE https://app.payout.one/api/v1/mtls/certificates/<thumbprint> \
  -H "Authorization: Bearer <TOKEN>"
```

### Revocation (by Payout)

Payout may also revoke a certificate if it has been compromised or if the contractual relationship ends. You will be notified by email and via webhook (`mtls_certificate.revoked`).

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
| `401 Unauthorized` | Missing or invalid Bearer token. |
| `403 Forbidden` | Certificate not `approved`, not owned by your account, or expired/revoked. |
| `404 Not Found` | Certificate with the given thumbprint not found (or not owned by your account). |
| `409 Conflict` | Certificate with the same thumbprint already imported. |
| `422 Unprocessable Entity` | Validation error (malformed PEM, key usage doesn't match the declared `type`, issuer not in Payout's trust store / unsupported QTSP, missing field, etc.). |
| TLS handshake refused | At the mTLS host: client certificate missing, expired, revoked, or not issued by a trusted QTSP. |

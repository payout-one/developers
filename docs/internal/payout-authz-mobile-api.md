# Payout Authz — Mobile API

`payout-authz` is the transaction-authorization service. It enrolls a user's
mobile device, issues challenges (login / withdrawal / batch withdrawal), pushes
them to the device, and verifies the device's **ES256 signature** when the user
approves. This page documents the HTTP API consumed by the **payout-authz-mobile**
Flutter app; the backend-facing endpoints (challenge creation, device listing) are
summarized at the end.

The machine-readable source of truth is the OpenAPI 3.1 spec in the
`payout-one/payout-authz-contracts` repository (`openapi/payout-authz.yaml`); this
page is its human-readable companion, and a Dart client can be generated from it
(`configs/dart.yaml`). When they disagree, the spec and the deployed service win.

## Base URL

Every path below is relative to the environment base URL, which already includes
the `/api` prefix.

| Environment | Base URL |
|-------------|----------|
| Production  | `https://authz.payout.one/api` |
| Test        | `https://authz-test.payout.one/api` |
| Sandbox     | `https://authz-sandbox.payout.one/api` |

All requests and responses are `application/json`.

## Authentication

There is **no `Authorization` / bearer header** on any mobile-facing endpoint.
Authentication is contextual, and the app enrolls and uses **two separate ES256
keypairs** for two separate purposes:

- **Approval key** (`public_key_pem`) — gated behind biometrics or a device
  credential. Signs `POST /approvals` (a body signature over the approval set —
  see [Signing an approval set](#signing-an-approval-set)).
- **Device / proof-of-possession (PoP) key** (`pop_public_key_pem`) — **not**
  gated behind biometrics or a device credential. Signs the `DevicePoP` request
  headers (`X-Device-Id`, `X-Timestamp`, `X-Nonce`, `X-Signature-Alg`,
  `X-Signature`) required by `GET /challenges`, self-service
  `POST /devices/{id}/revoke`, and `POST /devices/{id}/integrity` — see
  [Device proof-of-possession (PoP) headers](#device-proof-of-possession-pop-headers).

Both keys are required at enrollment; there is no fallback from one to the
other, and a PoP signature never authenticates an approval submission (or vice
versa). Separating the keys means polling for pending challenges — or a device
revoking itself — never triggers a biometric or device-credential prompt,
while every money-moving or consent decision still requires one.

Per endpoint:

- **Enrollment** — the app proves the user's identity by sending the OAuth 2.0
  access token (a JWT issued by PayoutID) in the request **body** as
  `access_token`. The service validates it against the PayoutID JWKS and derives
  `user_id` from it; the app never sends `user_id` at enrollment.
- **`GET /challenges`, self-service `POST /devices/{id}/revoke`,
  `POST /devices/{id}/integrity`** — `DevicePoP`: the app signs the request with
  the device/PoP key. No bearer token is issued or sent.
- **`POST /approvals`** — no header at all. Integrity is guaranteed by an
  **ES256 signature** (`signature_der`) over the canonical approval set,
  produced with the device's **approval key**.
- **Backend-facing endpoints** (challenge creation, device listing, and
  `POST /devices/{id}/revoke` when a backend service revokes on a user's
  behalf) — a bearer **ServiceToken**: an OAuth 2.0 client-credentials access
  token issued by `payout_id`, scoped `authz:challenge:write`. These are called
  server-to-server by `payout_merchant` / `payout_id`, never by the mobile app;
  see [Backend-facing endpoints](#backend-facing-endpoints-reference).

> [!TIP]
> Neither private key ever leaves the device. Both are generated on-device
> during enrollment; only the public keys (PEM) are uploaded. Approvals and
> PoP headers are signed locally.

## Enrollment

Enrollment is a two-step flow. Only **one device may be enrolled per user** at a
time — completing a new enrollment revokes the previously enrolled device (push +
`device.revoked` event), and the app on the old device force-clears its local
enrollment.

1. **Obtain an access token from PayoutID** via the OAuth 2.0 Authorization Code
   flow with PKCE. See [PayoutID OAuth2](/payout-id/oauth-new.md). The app scans a
   QR code that carries the `authorize_url`, completes the browser flow, and
   exchanges the `authorization_code` for an `access_token`.
2. **Complete enrollment** by posting the device's two public keys and push
   token.

### `POST /authn/enroll/complete`

Registers the device and stores its **two** ES256 public keys — a deliberate
two-key split, generated and held separately on-device, never the same key
used for both purposes:

- `public_key_pem` — the **approval key**, gated behind biometrics or a
  device credential. Verifies `POST /approvals` signatures.
- `pop_public_key_pem` — the **device proof-of-possession key**, not gated
  behind biometrics or a device credential. Verifies the `DevicePoP`
  (`X-Signature`) header on `GET /challenges`, self-service
  `POST /devices/{id}/revoke`, and `POST /devices/{id}/integrity`.

Both are required; the server does not accept a single shared key, and there
is no fallback from one to the other — a device enrolled without
`pop_public_key_pem` fails `DevicePoP` verification with `missing_pop_key`.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `access_token` | string | ✅ | OAuth access token (JWT) from PayoutID. Identifies the user. |
| `public_key_pem` | string | ✅ | Device ES256 (P-256) **approval** public key, PEM format. Biometric-/device-credential-gated; signs approval sets. |
| `pop_public_key_pem` | string | ✅ | Device ES256 (P-256) **proof-of-possession** public key, PEM format. Not gated behind biometrics or a device credential; signs the `DevicePoP` header. A separate keypair from `public_key_pem` — never reuse it. |
| `push_token` | string | ✅ | APNs token or FCM registration token. |
| `platform` | string | ✅ | `ios` or `android`. |
| `biometrics_enabled` | boolean | ✅ | Whether the approval key unlocks with biometrics. The app has no PIN of its own: when this is `false`, the OS device credential (passcode/PIN) is the fallback gate on the approval key, not an app-level PIN. |
| `device_name` | string | ➖ | Shown in device lists. |
| `attestation_json` | object | ➖ | Optional device attestation data. |

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...\n-----END PUBLIC KEY-----",
  "pop_public_key_pem": "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgBF...\n-----END PUBLIC KEY-----",
  "push_token": "fcm:dZx8vN3kQ2m...",
  "platform": "ios",
  "biometrics_enabled": true,
  "device_name": "iPhone 15 Pro"
}
```

**Response `201 Created`**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

Persist `device_id` on the device — it identifies the device on every subsequent
call.

**Errors**

| HTTP | `code` | When |
|------|--------|------|
| 400 | `invalid_request` | Missing `access_token`. |
| 400 | `validation_error` / `enrollment_error` | Invalid or incomplete device fields. |
| 401 | `invalid_token` | Missing, invalid, or expired `access_token`. |

## Challenge lifecycle

A challenge is created `pending`, is pushed to the enrolled device, and lives for a
**3-minute TTL** with **2 approval attempts**. It ends in a terminal state:

| Status | Meaning |
|--------|---------|
| `pending` | Awaiting the user's decision. |
| `approved` | User approved (signature verified). |
| `rejected` | User rejected. |
| `expired` | TTL (3 minutes) elapsed. |

Each failed approval attempt (e.g. a signature mismatch) decrements
`attempts_left`. When it reaches 0, further attempts are refused.

### Challenge object

Returned by the list and get endpoints and echoed on creation.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | Challenge id. |
| `type` | string | `login`, `withdrawal`, or `withdrawal_batch`. |
| `status` | string | See table above. |
| `expires_at` | date-time | ISO 8601, 3 minutes after creation. |
| `attempts_left` | integer | Starts at 2. |
| `payload_hash` | string | Lowercase hex SHA-256 of the challenge's canonical authorization view (`{ payload, items }` — see [Signing an approval set](#signing-an-approval-set)). The app should independently **recompute** this from the `payload`/`items` it renders to the user rather than trust-copy this field, since it's what binds the approval signature to what the user actually saw. |
| `payload` | object | Type-specific details (see below). |
| `reference` | string | Human-readable code shown to the user (`txn_id`, `batch_id`, or a generated `LOGIN-XXXXXXXX`). |
| `items_count` | integer | Present only for `withdrawal_batch`. |
| `items` | array | Present only for `withdrawal_batch`: the line items, `{ amount, currency, iban }` each, already sorted the same way `payload_hash` requires (ascending by each item's own canonical-bytes string) — see [Signing an approval set](#signing-an-approval-set). |
| `metadata` | object | Present only for `withdrawal_batch`: `{ batch_id, amount, currency }`. |

`payload` contents by type:

- **login** — `{ type, reference, requested_at }` plus any caller metadata.
- **withdrawal** — `{ type, reference, amount, currency, iban, name?, requested_at }`.
- **withdrawal_batch** — `{ type, reference, batch_id, total_amount, currency, items_count, requested_at }`.

## Mobile endpoints

### `GET /challenges`

Requires **`DevicePoP`** — see
[Device proof-of-possession (PoP) headers](#device-proof-of-possession-pop-headers).
Lists the **pending** challenges for the caller's authenticated device;
identity comes from the PoP signature, not from a query/body param (the
signature does not cover the query string). Use it to reconcile state on app
foreground or after a missed push. Expired challenges are transitioned to
`expired` server-side and are not returned.

An optional `device_id` query param is accepted only as a same-device sanity
check: if present it must equal the authenticated device's id, otherwise the
request is rejected with `403 device_mismatch` — a caller can't use its own
valid PoP signature to ask for another device's challenges by tampering with
the query string.

**Response `200 OK`**

```json
{
  "challenges": [
    {
      "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "type": "withdrawal",
      "status": "pending",
      "expires_at": "2026-07-02T14:35:00Z",
      "attempts_left": 2,
      "payload_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
      "reference": "TXN-2025-001234",
      "payload": {
        "type": "withdrawal",
        "reference": "TXN-2025-001234",
        "amount": "150.00",
        "currency": "EUR",
        "iban": "SK8975000000000012345671",
        "requested_at": "2026-07-02T14:32:00Z"
      }
    }
  ]
}
```

**Errors**

Auth failures use the `{"error": "<reason>"}` shape, not `{"code", "message"}`
— see [Device proof-of-possession (PoP) headers](#device-proof-of-possession-pop-headers).

| HTTP | `error` | When |
|------|---------|------|
| 401 | `missing_pop_headers` | One or more `X-Device-Id` / `X-Timestamp` / `X-Nonce` / `X-Signature-Alg` / `X-Signature` headers is missing or malformed. |
| 401 | `unsupported_signature_algorithm` | `X-Signature-Alg` is not `ES256`. |
| 401 | `stale_timestamp` | `X-Timestamp` is outside the freshness window. |
| 401 | `replayed` | `X-Nonce` was already used within the replay window. |
| 401 | `invalid_device` | Unknown or revoked device id. |
| 401 | `missing_pop_key` | The device has no `pop_public_key_pem` on record (legacy enrollment predating the two-key split). |
| 401 | `invalid_signature` | ES256 verification against the device's PoP key failed. |
| 403 | `device_mismatch` | The `device_id` query param doesn't match the authenticated device. |

### `POST /approvals`

Approves and/or rejects one or more challenges in a single **ES256-signed**
request. See [Signing an approval set](#signing-an-approval-set) for how the
signature is built.

> [!WARNING]
> **Breaking (v2.0.0).** The signed set now binds each decision to the exact
> transaction payload the user was shown (`payload_hash`) and adds a
> whole-set `timestamp` + `nonce`. Signatures built against the old 3-key
> object (`challenge_id`/`decision`/`user_id` only) no longer reproduce the
> server's canonical bytes and are rejected with `401 invalid_signature`.
> `payout-authz` and `payout-authz-mobile` must deploy this together.

**Request body**

| Field | Type | Notes |
|-------|------|-------|
| `device_id` | uuid | The enrolled device. |
| `approvals` | array | 1–50 items. Each: `{ challenge_id, decision, payload_hash }` where `decision` is `approve` or `reject` and `payload_hash` is the SHA-256 hex digest computed per [Signing an approval set](#signing-an-approval-set). |
| `signature_alg` | string | Must be `ES256`. |
| `signature_der` | string | Base64-encoded DER ECDSA signature over the canonical **signed set** (`{ approvals, timestamp, nonce }`, each approval including `payload_hash`). |
| `timestamp` | integer | Unix seconds when the set was signed. Signed as a JSON **integer**, not a string. Must be within the server's freshness window (120s by default, plus 5s of allowed clock skew) or the whole set is rejected. |
| `nonce` | string | Client-generated single-use value. A repeat within the replay window rejects the whole set. |

> [!NOTE]
> `challenge_id`, `decision`, and `payload_hash` are read from each item.
> `payload_hash` is recomputed server-side from the **stored** challenge and
> verified; a mismatch fails only that item (`payload_mismatch`), reported in
> `errors` below — it does not by itself invalidate the rest of the set's
> signature. Any other field an item includes (e.g. `user_id`) is ignored —
> the `user_id` in the signed message is always the enrolled owner's id,
> injected server-side. See the signing section for the full algorithm.

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "approvals": [
    {
      "challenge_id": "00000000-0000-0000-0000-000000000002",
      "decision": "approve",
      "payload_hash": "772bdcf2b507bc072c0f7a27e6733a163df5f908b906ff3611c57139a0625981"
    },
    {
      "challenge_id": "00000000-0000-0000-0000-000000000001",
      "decision": "reject",
      "payload_hash": "4ba67e21b1e9486465170eece00474686d15542855d28ba38fd68e6cbc938a42"
    }
  ],
  "signature_alg": "ES256",
  "signature_der": "MEUCIQD6bU4B78zNE+q7KQpLlHkYeFBZ4/+K2ljjms7kDGGPxgIgMZRU4lVTNy7x6bJr/6v6/nawD2dc2B1suOObJO4gIO8=",
  "timestamp": 1770000000,
  "nonce": "vector-nonce-001"
}
```

**Response `200 OK`**

```json
{
  "approved_ids": ["00000000-0000-0000-0000-000000000002"],
  "rejected_ids": ["00000000-0000-0000-0000-000000000001"],
  "errors": []
}
```

> [!NOTE]
> Per-challenge failures (e.g. one expired challenge in the set) are reported in
> `errors` **with HTTP 200** — inspect the body, not just the status. A non-200
> status means the whole set was rejected. Each `errors` item is
> `{ challenge_id, code, message }`, where `code` is one of `not_found`,
> `expired`, `attempts_exhausted`, `invalid_state`, `unauthorized`,
> `invalid_decision`, or `payload_mismatch` (the signed `payload_hash` didn't
> match the server-recomputed value for the stored challenge).

**Errors (whole set rejected)**

| HTTP | `code` | When |
|------|--------|------|
| 400 | `invalid_approval_set` | Malformed set (including a missing/malformed `payload_hash`, `timestamp`, or `nonce`). |
| 400 | `unsupported_signature_algorithm` | `signature_alg` is not `ES256`. |
| 401 | `invalid_signature` | ES256 verification failed. |
| 401 | `device_revoked` | The device has been revoked. |
| 401 | `stale_timestamp` | `timestamp` is outside the freshness window (120s, +5s clock skew). |
| 401 | `replayed` | `nonce` was already used within the replay window. |
| 404 | `not_found` | Unknown `device_id`. |

### `POST /devices/{id}/revoke`

Revokes the device so it can no longer approve challenges. Sends a push that forces
the app to clear local enrollment and publishes a `device.revoked` event
(downstream services fall back to TOTP). The app calls this during un-enroll. The
request body is empty.

Requires **`DevicePoP`** (self-revoke — see
[Device proof-of-possession (PoP) headers](#device-proof-of-possession-pop-headers))
**or** a backend-facing `ServiceToken`. A `DevicePoP` caller may only revoke its
own device: the path `{id}` must equal the authenticated device's id, otherwise
the request is rejected with `403 forbidden` — a device can't use its own valid
PoP signature to revoke a different device.

**Response `200 OK`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "revoked_at": "2026-07-02T14:40:00Z",
  "message": "Device revoked successfully"
}
```

**Errors**

| HTTP | `code` / `error` | When |
|------|------------------|------|
| 400 | `already_revoked` | Device is already revoked. |
| 401 | *(DevicePoP failure reasons — see [Device proof-of-possession (PoP) headers](#device-proof-of-possession-pop-headers))* | Missing/malformed PoP headers, bad signature, stale timestamp, replayed nonce, or an unknown/revoked PoP device — when using `DevicePoP`. |
| 403 | `forbidden` | A `DevicePoP`-authenticated device attempted to revoke a different device id. |
| 404 | `not_found` | Unknown device. |
| 500 | `revocation_failed` | Update failed. |

### `POST /devices/{id}/integrity`

Requires **`DevicePoP`** — see
[Device proof-of-possession (PoP) headers](#device-proof-of-possession-pop-headers).
Because this request carries a body, the PoP signature's `body_sha256` covers
the raw JSON request body.

The app self-reports a runtime-integrity verdict (root/jailbreak/hook/emulator/
tamper detection — e.g. from freerasp) for the device identified by `{id}`,
which must equal the authenticated device's id (otherwise `403
device_mismatch`).

> [!NOTE]
> **Warn-not-block.** A compromised verdict is never rejected — the server
> always records the report (caching the latest verdict on the device record,
> and writing an audit-log entry keyed by device + user when the compromised
> state changes) and responds `200`. This endpoint does not gate any
> operation; it exists purely to give operators visibility into which
> enrolled devices are running on compromised hardware/OS.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `platform` | string | ✅ | `ios` or `android`. Compared against the device's enrolled platform as a data-quality signal; a mismatch is recorded, never rejected. |
| `threats` | array of string | ✅ | Threat identifiers detected on-device (e.g. freerasp threat names); `[]` when clean. Non-string entries are dropped and the list is capped server-side — never rejected for being too long or malformed. |
| `compromised` | boolean | ✅ | Overall compromised verdict for this report. |
| `attestation` | object \| null | ➖ | Optional opaque platform-attestation blob (Play Integrity / App Attest). Accepted and verified server-side on receipt; only the verification outcome is recorded — the raw blob is never persisted. |

```json
{
  "platform": "android",
  "threats": ["privilegedAccess", "hooks"],
  "compromised": true,
  "attestation": null
}
```

**Response `200 OK`**

Always returned on success — this endpoint never blocks a compromised report.

```json
{
  "recorded": true,
  "compromised": true
}
```

**Errors**

| HTTP | `code` / `error` | When |
|------|------------------|------|
| 400 | `invalid_request` | Missing or invalid `platform` / `compromised` / `threats`. |
| 401 | *(DevicePoP failure reasons)* | Missing/malformed PoP headers, bad signature, stale timestamp, replayed nonce, or an unknown/revoked PoP device. |
| 403 | `device_mismatch` | A `DevicePoP`-authenticated device attempted to report integrity for a different device id. |
| 500 | `record_failed` | Update failed. |

## Signing an approval set

> [!WARNING]
> **Breaking (v2.0.0).** The signed set now includes a per-item `payload_hash`
> and a top-level `timestamp`/`nonce`. This is a byte-for-byte cross-language
> contract, pinned by `apps/core/test/fixtures/approval_vectors.json` in the
> `payout-authz` repo — copy that fixture into the mobile repo and assert
> against it in a Dart test. A single differing byte (key order, whitespace,
> number formatting, an un-normalized amount string) produces a different
> hash/signature and the server rejects it with `401 invalid_signature` (or,
> for a per-item `payload_hash` mismatch alone, `payload_mismatch` on that
> item).

The `signature_der` in `POST /approvals` is an **ES256 (ECDSA / P-256 / SHA-256)**
signature over the **canonical JSON** of the signed set, produced with the
device's **approval** private key (never the PoP key — see
[Authentication](#authentication)). Build it exactly as the server does:

### 1. Compute `payload_hash` for every challenge being decided

`payload_hash` is the lowercase hex SHA-256 digest of the canonical bytes of
the challenge's **authorization view**:

```
{ "payload": <the challenge's `payload` object, exactly as returned by
               GET /challenges / the challenge object>,
  "items":   <line items, see below> }
```

- **`login` and `withdrawal` challenges**: `items` is always `[]`.
- **`withdrawal_batch` challenges**: `items` is the array of
  `{ "amount", "currency", "iban" }` objects from the challenge's `items`
  field (see [Challenge object](#challenge-object)), **sorted ascending by
  each item's own canonical-bytes string** — i.e. by the UTF-8 bytes of that
  single item's `{"amount":...,"currency":...,"iban":...}` canonical JSON,
  compared byte-by-byte (NOT by array/DB order, and NOT a numeric sort on
  `amount`). The `GET /challenges` response already returns `items` in this
  sorted order, but don't rely on that — re-derive the sort independently;
  this is the single biggest cross-language determinism risk.
- **Amounts are decimal-valued strings, hashed verbatim.** `payload.amount`,
  `payload.total_amount`, and each batch item's `amount` are canonical
  decimal strings as stored/returned by the server (e.g. `"10.50"`, never
  `"10.5"` or scientific notation). Hash the **exact string** the API
  returned — never re-parse it into a number, reformat it, round it, or
  strip/add trailing zeros. A client-side reformat is the most likely source
  of a byte-parity break.

Canonicalize with the same rule used everywhere in this doc: JSON with **all
object keys sorted lexicographically, recursively**, and **no insignificant
whitespace**.

Worked examples (from the fixture — reproduce these exactly):

```
# login challenge, no items
{"items":[],"payload":{"reference":"LOGIN-VEC001","requested_at":"2026-07-10T12:00:00Z","type":"login"}}
→ payload_hash = 4ba67e21b1e9486465170eece00474686d15542855d28ba38fd68e6cbc938a42

# single withdrawal, no items
{"items":[],"payload":{"amount":"10.50","currency":"EUR","iban":"DE89370400440532013000","name":"Jane Doe","reference":"WD-VEC001","requested_at":"2026-07-10T12:05:00Z","type":"withdrawal"}}
→ payload_hash = 772bdcf2b507bc072c0f7a27e6733a163df5f908b906ff3611c57139a0625981

# withdrawal_batch, 2 items — note items are sorted 30.00 before 70.00
# ("3" < "7" in each item's own canonical-bytes string), NOT input order
{"items":[{"amount":"30.00","currency":"EUR","iban":"SK8975000000000012345671"},{"amount":"70.00","currency":"EUR","iban":"SK3112000000198742637541"}],"payload":{"batch_id":"BATCH-VEC001","currency":"EUR","items_count":2,"reference":"BATCH-VEC001","requested_at":"2026-07-10T12:10:00Z","total_amount":"100.00","type":"withdrawal_batch"}}
→ payload_hash = b638bf41ebdbe32b07c6b2682aa9ac3a2caf3008c1b5ed532ae19f9cdd0d7d8e
```

### 2. Build and sign the approvals wrapper

1. For each decision, build the object
   `{ "challenge_id": <id>, "decision": <approve|reject>, "payload_hash": <from step 1>, "user_id": <userId> }`,
   where `user_id` is the enrolled user's id (returned at enrollment).
2. Sort the objects **ascending by `challenge_id`**.
3. Wrap them with the whole-set fields:
   `{ "approvals": [ ...sorted objects... ], "timestamp": <unix seconds, integer>, "nonce": <string> }`.
   `timestamp` MUST be a JSON **integer** in the signed bytes (not a numeric
   string). `nonce` is a client-generated single-use string.
4. Canonicalize: serialize to JSON with all object keys sorted
   lexicographically, recursively, and no insignificant whitespace.
5. Sign the UTF-8 bytes of that string with ES256. Base64-encode the DER
   signature into `signature_der`.

For the request-body example above (user `00000000-0000-0000-0000-0000000000aa`,
`timestamp` `1770000000`, `nonce` `vector-nonce-001`), the exact string that
gets signed — byte-for-byte identical to `signed_set_vector.canonical_bytes`
and `verify_vector.signing_input` in the fixture — is:

```json
{"approvals":[{"challenge_id":"00000000-0000-0000-0000-000000000001","decision":"reject","payload_hash":"4ba67e21b1e9486465170eece00474686d15542855d28ba38fd68e6cbc938a42","user_id":"00000000-0000-0000-0000-0000000000aa"},{"challenge_id":"00000000-0000-0000-0000-000000000002","decision":"approve","payload_hash":"772bdcf2b507bc072c0f7a27e6733a163df5f908b906ff3611c57139a0625981","user_id":"00000000-0000-0000-0000-0000000000aa"}],"nonce":"vector-nonce-001","timestamp":1770000000}
```

The `signature_der` in the request-body example above is a real, verifiable
ES256 signature over this exact string (the fixture's `verify_vector`
includes the matching test-only private/public keypair, so a Dart
implementation can both re-sign this input and verify the committed
signature against it).

> [!WARNING]
> The server recomputes this string — including recomputing every
> `payload_hash` **from the stored challenge**, never from the client's value
> — and **injects `user_id` from the device record**. If your local
> canonicalization differs (key order, whitespace, a different `user_id`, or
> a mis-derived `payload_hash`), verification fails with `401
> invalid_signature`, or, for a `payload_hash`-only mismatch on one item,
> that item fails with `payload_mismatch` while the rest of the set is still
> processed. Match the canonical form byte-for-byte.

### 3. Freshness and replay

- `timestamp` must be within **120 seconds** of the server's clock (plus 5s
  of allowed clock skew into the future) or the whole set is rejected with
  `401 stale_timestamp`, checked before any challenge is touched.
- A `nonce` already seen within twice that window is rejected with `401
  replayed`.
- An exact byte-identical resubmission (same approvals, `payload_hash`es,
  `timestamp`, and `nonce` as a previously recorded approval) is treated as
  an idempotent retry — it returns the original cached result and skips the
  nonce-replay check, so a legitimate retry after a dropped response doesn't
  fail as a replay.

## Device proof-of-possession (PoP) headers

`GET /challenges`, self-service `POST /devices/{id}/revoke`, and
`POST /devices/{id}/integrity` require **`DevicePoP`**: the app signs the
request with its enrolled **device/PoP key** (`pop_public_key_pem` — never the
approval key `public_key_pem`; a PoP signature never authenticates
`POST /approvals`, and an approval signature never satisfies `DevicePoP`). No
bearer token is issued or sent — the app doesn't hold anything long-lived to
present; it signs each request fresh.

OpenAPI has no way to express a multi-header signature scheme, so all five of
the following headers must be present together:

| Header | Notes |
|--------|-------|
| `X-Device-Id` | The enrolled device id. |
| `X-Timestamp` | Integer unix seconds. Rejected with `401 stale_timestamp` if outside a small freshness window (server-configured; default **60s**, plus 5s of allowed clock skew into the future). |
| `X-Nonce` | Client-generated single-use value. A repeat within the freshness window is rejected with `401 replayed`. |
| `X-Signature-Alg` | Must be the literal string `ES256`. |
| `X-Signature` | Base64-encoded DER ECDSA signature (the same encoding `POST /approvals`' `signature_der` uses). |

### Signing input

The signature covers the **canonical JSON** (object keys sorted
lexicographically, recursively, no insignificant whitespace — the same rule
used in [Signing an approval set](#signing-an-approval-set)) of:

```
{"method": "<HTTP method, uppercase>",
 "path": "<request path, no query string, including the `/api` prefix — i.e. what the server sees as `conn.request_path`>",
 "device_id": "<X-Device-Id>",
 "timestamp": <X-Timestamp, as an integer>,
 "nonce": "<X-Nonce>",
 "body_sha256": "<lowercase hex SHA-256 of the raw request body>"}
```

- `method` is upper-cased (`GET`, `POST`).
- `path` excludes the query string. It includes the `/api` prefix — e.g.
  `/api/challenges`, `/api/devices/550e8400-e29b-41d4-a716-446655440000/revoke`,
  `/api/devices/550e8400-e29b-41d4-a716-446655440000/integrity` — not just the
  path relative to this document's [Base URL](#base-url) table.
- `body_sha256` is the lowercase hex SHA-256 digest of the **raw** request
  body bytes. For a body-less request (`GET /challenges`, self-service
  `POST /devices/{id}/revoke`, whose body is empty) this is the SHA-256 of the
  empty string. For `POST /devices/{id}/integrity`, it's the hash of the raw
  JSON body bytes actually sent — hash before any re-serialization, since a
  different byte sequence produces a different hash and the signature won't
  verify.

Sign the UTF-8 bytes of the canonical string with ES256 (ECDSA / P-256 /
SHA-256) using the device/PoP private key. Base64-encode the DER signature
into `X-Signature`.

The server verifies against the device's stored `pop_public_key_pem` and
rejects any failure (missing/malformed header, unsupported algorithm, stale
timestamp, replayed nonce, unknown or revoked device, a device with no PoP key
on record, or a bad signature) with `401` and `{"error": "<reason>"}`.

### Freshness and replay

- `X-Timestamp` must be within the server's freshness window (default **60
  seconds**, plus 5s of allowed clock skew into the future) or the request is
  rejected with `401 stale_timestamp`.
- An `X-Nonce` already seen within twice that window is rejected with `401
  replayed`.

> [!NOTE]
> This window and default (60s) are narrower than the 120s used for
> `POST /approvals`' `timestamp`/`nonce` — the two freshness checks are
> independently configured and not interchangeable.

## Push notifications

The device's push token (`push_token`) is registered once, during
`POST /authn/enroll/complete`. The service then delivers challenge events to the
device (APNs for iOS, FCM for Android): a new challenge to display, and a
cancellation when a pending challenge is deleted server-side. The app does not
register the token through any separate endpoint.

## Backend-facing endpoints (reference)

These are called server-to-server by `payout_merchant` / `payout_id`, not by the
mobile app, and require a bearer **ServiceToken** — an OAuth 2.0
client-credentials access token issued by `payout_id`, RS256/JWKS-verified and
scoped `authz:challenge:write` — sent as `Authorization: Bearer <token>`. They
are fully documented in the OpenAPI spec.

`POST /devices/{id}/revoke` also accepts a `ServiceToken` (in addition to
`DevicePoP`, self-revoke only) so a backend service can revoke any device on a
user's behalf — see the mobile endpoints section above.

| Endpoint | Purpose |
|----------|---------|
| `POST /challenges` | Create a challenge, dispatched by `type`. |
| `POST /challenges/login` | Create a login challenge. |
| `POST /challenges/withdrawal` | Create a single-withdrawal challenge. |
| `POST /challenges/withdrawal_batch` | Create a batch-withdrawal challenge. |
| `GET /challenges/{id}` | Fetch a single challenge (returns `expired` past TTL). |
| `DELETE /challenges/{id}` | Cancel a pending challenge (pushes a removal). |
| `GET /devices?user_id={id}` | List all devices (active + revoked) for a user. |
| `GET /devices/{id}` | Device details. |
| `GET /users/{user_id}/devices` | List a user's active devices. |

Challenge-creation requests accept an optional `Idempotency-Key` header: repeating
a request with the same key for the same user returns the existing challenge
without creating a duplicate or dispatching a second push.

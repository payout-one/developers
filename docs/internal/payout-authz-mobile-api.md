# Payout Authz — Mobile API

> [!WARNING]
> **Internal, unlisted page.** This document is intentionally not linked from the
> sidebar, top navigation, or search. It is reachable only via its direct
> `#/internal/payout-authz-mobile-api` link. Treat the URL as internal and do not
> link it from public pages.

`payout-authz` is the transaction-authorization service. It enrolls a user's
mobile device, issues challenges (login / withdrawal / batch withdrawal), pushes
them to the device, and verifies the device's **ES256 signature** when the user
approves. This page documents the HTTP API consumed by the **payout-authz-mobile**
Flutter app; the backend-facing endpoints (challenge creation, device listing) are
summarized at the end.

> [!NOTE]
> **Source of truth.** The machine-readable contract is the OpenAPI 3.1 spec in
> the `payout-one/payout-authz-contracts` repository
> (`openapi/payout-authz.yaml`). This page is a human-readable companion; when the
> two disagree, the OpenAPI file and the deployed service win. A Dart client can be
> generated from that spec (`configs/dart.yaml`).

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

There is **no `Authorization` / bearer header** on any endpoint. Authentication is
contextual:

- **Enrollment** — the app proves the user's identity by sending the OAuth 2.0
  access token (a JWT issued by PayoutID) in the request **body** as
  `access_token`. The service validates it against the PayoutID JWKS and derives
  `user_id` from it; the app never sends `user_id` at enrollment.
- **Approvals** — integrity is guaranteed by an **ES256 signature** over the
  approval set, produced with the device's enrolled private key. The device is
  identified by `device_id`.
- **Challenge polling and device revoke** — device-bound: the app sends the
  `device_id` it received at enrollment.

> [!TIP]
> The private key never leaves the device. It is generated on-device during
> enrollment; only the public key (PEM) is uploaded. Approvals are signed locally.

## Enrollment

Enrollment is a two-step flow. Only **one device may be enrolled per user** at a
time — completing a new enrollment revokes the previously enrolled device (push +
`device.revoked` event), and the app on the old device force-clears its local
enrollment.

1. **Obtain an access token from PayoutID** via the OAuth 2.0 Authorization Code
   flow with PKCE. See [PayoutID OAuth2](/payout-id/oauth-new.md). The app scans a
   QR code that carries the `authorize_url`, completes the browser flow, and
   exchanges the `authorization_code` for an `access_token`.
2. **Complete enrollment** by posting the device's public key and push token.

### `POST /authn/enroll/complete`

Registers the device and stores its ES256 public key.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `access_token` | string | ✅ | OAuth access token (JWT) from PayoutID. Identifies the user. |
| `public_key_pem` | string | ✅ | Device ES256 (P-256) public key, PEM format. |
| `push_token` | string | ✅ | APNs token or FCM registration token. |
| `platform` | string | ✅ | `ios` or `android`. |
| `biometrics_enabled` | boolean | ✅ | Whether approvals unlock with biometrics. |
| `device_name` | string | ➖ | Shown in device lists. |
| `pin_hash` | string | ⚠️ | Client-computed hash of the device PIN. **Required when `biometrics_enabled` is `false`.** The raw PIN never leaves the device. |
| `attestation_json` | object | ➖ | Optional device attestation data. |

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...\n-----END PUBLIC KEY-----",
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
| `payload_hash` | string | Lowercase hex SHA-256 of the JSON payload. |
| `payload` | object | Type-specific details (see below). |
| `reference` | string | Human-readable code shown to the user (`txn_id`, `batch_id`, or a generated `LOGIN-XXXXXXXX`). |
| `items_count` | integer | Present only for `withdrawal_batch`. |
| `metadata` | object | Present only for `withdrawal_batch`: `{ batch_id, amount, currency }`. |

`payload` contents by type:

- **login** — `{ type, reference, requested_at }` plus any caller metadata.
- **withdrawal** — `{ type, reference, amount, currency, iban, name?, requested_at }`.
- **withdrawal_batch** — `{ type, reference, batch_id, total_amount, currency, items_count, requested_at }`.

## Mobile endpoints

### `GET /challenges?device_id={deviceId}`

Lists the **pending** challenges for the user that owns `device_id`. Use it to
reconcile state on app foreground or after a missed push. Expired challenges are
transitioned to `expired` server-side and are not returned.

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

| HTTP | `code` | When |
|------|--------|------|
| 400 | `invalid_request` | Missing `device_id`. |
| 401 | `device_revoked` | The device has been revoked. |
| 404 | `device_not_found` | Unknown `device_id`. |

### `POST /approvals`

Approves and/or rejects one or more challenges in a single **ES256-signed**
request. See [Signing an approval set](#signing-an-approval-set) for how the
signature is built.

**Request body**

| Field | Type | Notes |
|-------|------|-------|
| `device_id` | uuid | The enrolled device. |
| `approvals` | array | 1–50 items. Each: `{ challenge_id, decision }` where `decision` is `approve` or `reject`. |
| `signature_alg` | string | Must be `ES256`. |
| `signature_der` | string | Base64-encoded DER ECDSA signature over the canonical approval set. |

> [!NOTE]
> Only `challenge_id` and `decision` are read from each item. Any extra fields the
> app includes (e.g. `payload_hash`, `user_id`) are ignored by the server. The
> `user_id` used in the signed message is injected server-side from the device
> record — see the signing section.

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "approvals": [
    { "challenge_id": "d290f1ee-6c54-4b01-90e6-d701748f0851", "decision": "approve" },
    { "challenge_id": "b7d3e8c2-4a1f-4e9d-8c5b-2f1a3d6e8b9c", "decision": "reject" }
  ],
  "signature_alg": "ES256",
  "signature_der": "MEUCIQD1KrQvSKJh0TcMwxKkqPp3OV8r9fZ2xY3wB5kA7cD8eQIgXnY9zL2mP4qR6sT8uV0wX2yA4bC6dE8fG0hI2jK4lM6="
}
```

**Response `200 OK`**

```json
{
  "approved_ids": ["d290f1ee-6c54-4b01-90e6-d701748f0851"],
  "rejected_ids": ["b7d3e8c2-4a1f-4e9d-8c5b-2f1a3d6e8b9c"],
  "errors": []
}
```

> [!NOTE]
> Per-challenge failures (e.g. one expired challenge in the set) are reported in
> `errors` **with HTTP 200** — inspect the body, not just the status. A non-200
> status means the whole set was rejected. Each `errors` item is
> `{ challenge_id, code, message }`, where `code` is one of `not_found`,
> `expired`, `attempts_exhausted`, `invalid_state`, `unauthorized`, or
> `invalid_decision`.

**Errors (whole set rejected)**

| HTTP | `code` | When |
|------|--------|------|
| 400 | `invalid_approval_set` | Malformed set. |
| 400 | `unsupported_signature_algorithm` | `signature_alg` is not `ES256`. |
| 401 | `invalid_signature` | ES256 verification failed. |
| 401 | `device_revoked` | The device has been revoked. |
| 404 | `not_found` | Unknown `device_id`. |

### `POST /devices/{id}/revoke`

Revokes the device so it can no longer approve challenges. Sends a push that forces
the app to clear local enrollment and publishes a `device.revoked` event
(downstream services fall back to TOTP). The app calls this during un-enroll. The
request body is empty.

**Response `200 OK`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "revoked_at": "2026-07-02T14:40:00Z",
  "message": "Device revoked successfully"
}
```

**Errors**

| HTTP | `code` | When |
|------|--------|------|
| 400 | `already_revoked` | Device is already revoked. |
| 404 | `not_found` | Unknown device. |
| 500 | `revocation_failed` | Update failed. |

## Signing an approval set

The `signature_der` in `POST /approvals` is an **ES256 (ECDSA / P-256 / SHA-256)**
signature over the **canonical JSON** of the approval set, produced with the
device's private key. Build the signed message exactly as the server does:

1. For each decision, build the object
   `{ "challenge_id": <id>, "decision": <approve|reject>, "user_id": <userId> }`,
   where `user_id` is the enrolled user's id (returned at enrollment).
2. Sort the objects **ascending by `challenge_id`**.
3. Wrap them: `{ "approvals": [ ...sorted objects... ] }`.
4. Canonicalize: serialize to JSON with **all object keys sorted lexicographically,
   recursively**, and **no insignificant whitespace**.
5. Sign the UTF-8 bytes of that string with ES256. Base64-encode the DER signature
   into `signature_der`.

For the two-item example above (user `7c9e6679-7425-40de-944b-e07fc1f90ae7`), the
exact string that gets signed is:

```json
{"approvals":[{"challenge_id":"b7d3e8c2-4a1f-4e9d-8c5b-2f1a3d6e8b9c","decision":"reject","user_id":"7c9e6679-7425-40de-944b-e07fc1f90ae7"},{"challenge_id":"d290f1ee-6c54-4b01-90e6-d701748f0851","decision":"approve","user_id":"7c9e6679-7425-40de-944b-e07fc1f90ae7"}]}
```

> [!WARNING]
> The server recomputes this string and **injects `user_id` from the device
> record**. If your local canonicalization differs (key order, whitespace, or a
> different `user_id`), verification fails with `401 invalid_signature`. Match the
> canonical form byte-for-byte.

## Push notifications

The device's push token (`push_token`) is registered once, during
`POST /authn/enroll/complete`. The service then delivers challenge events to the
device (APNs for iOS, FCM for Android): a new challenge to display, and a
cancellation when a pending challenge is deleted server-side. The app does not
register the token through any separate endpoint.

## Backend-facing endpoints (reference)

These are called server-to-server by `payout_merchant` / `payout_id`, not by the
mobile app. They are fully documented in the OpenAPI spec.

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

# Payment instructions (manual bank transfer)

Retrieves the data your customer needs to pay a checkout manually via bank transfer — recipient name, IBAN, local account number (CZ/SK), variable symbol, amount, currency and a ready-to-render QR code. No email is sent by this endpoint; it is intended for cases where you want to render the instructions in your own UI (invoice, thank-you page, PDF, etc.).

## Prerequisites

- The merchant account has **bank transfer** enabled for the checkout's currency. If not, the endpoint returns `409`. Enabling bank transfer is done by Payout support / in backoffice.

The endpoint returns one set of payment instructions per call — beneficiary, IBAN, variable symbol and a QR code matching the standard used in the checkout currency's country. The customer scans/uses it without needing to choose anything.

## Flow

1. Generate api key and secret
   * You can do it in backoffice ([Sandbox](https://sandbox.payout.one/developers/keys/new) or [Production](https://app.payout.one/developers/keys/new)) after you have already created account.

2. Make authorization call to get Bearer token

   ```bash
   curl --location --request POST 'https://sandbox.payout.one/api/v1/authorize' \
   --header 'Content-Type: application/json' \
   --header 'Accept: application/json' \
   --data-raw '{
    "client_id": "DC995618-7ED8-4070-9DA0-48B6F86551C3",
    "client_secret": "q3dpHpYtDrH-KmGD4HMn5OTEx6IsZPBokQ8CqMONWqMSEePWy9bXd3Ua3KvO7f6C"
   }'
   ```
   Response of this call looks like this:
   ```json
   {
    "token": "SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgWnBcvEfet1jIr9OPF984RGTKu-8HcHPQKJitk_kJKiU",
    "valid_for": 6000
   }
   ```

3. Create a checkout in the usual way (see [Simple payment](/payment-gateway/use-cases/simple-payment.md)). Keep the returned `id` — you will need it in the next step.

4. Call the `payment_instructions` endpoint with the checkout id. It's a GET HTTP call that requires only the Authorization header with the Bearer token from step 2.

   ```bash
   curl --location --request GET 'https://sandbox.payout.one/api/v1/checkouts/141447/payment_instructions' \
   --header 'Authorization: Bearer SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgA.WnBcvEfet2jJr4OPF984RGTKu-8HcHPQKJitk_kJKiU' \
   --header 'Accept: application/json'
   ```

5. Process the response

   ```json
   {
     "recipient_name": "Payout a.s.",
     "iban": "SK3883300000003175133001",
     "account_number": "000000-3175133001/8330",
     "variable_symbol": "8430300911",
     "amount": "0.0100",
     "currency": "EUR",
     "qr_code": "iVBORw0KGgoAAAANSUhEUgAAAX8AAAHBCAYAAACBh..."
   }
   ```

   | Field | Description |
   |---|---|
   | `recipient_name` | Name of the beneficiary the customer should send the money to. |
   | `iban` | Beneficiary IBAN in international format. |
   | `account_number` | Beneficiary account in **local format** (`prefix-account/bank_code`). Currently filled for Czech (CZ) and Slovak (SK) IBANs; `null` for other countries. |
   | `variable_symbol` | Variable symbol the customer must include in the transfer. It binds the incoming payment to the checkout. |
   | `amount` | Total amount to transfer, decimal string (e.g. `"0.0100"`). |
   | `currency` | ISO 4217 currency code. |
   | `qr_code` | Base64-encoded PNG of the payment QR. Render directly with `<img src="data:image/png;base64,${qr_code}" />`. |

   > [!NOTE]
   > The QR is cached server-side, so repeated calls for the same checkout return the same image without hitting the upstream QR generator again.

## Error responses

| HTTP | Error | Cause |
|---|---|---|
| `401` | `Unauthorized access. Check your token.` | Missing or invalid Bearer token. |
| `403` | `Forbidden` | The checkout does not belong to the authenticated account. |
| `404` | `Not Found` | Checkout with given `id` does not exist. |
| `409` | `Bank transfer not enabled for this account.` | The merchant account has no active bank-transfer payment method for the checkout currency. Enable it in backoffice. |
| `410` | `Checkout has expired.` | The checkout's `will_expire_at` has passed. Create a new checkout. |
| `422` | `No bank account available for this currency.` | No beneficiary bank account is available for the checkout currency. Contact Payout support. |
| `500` | `Failed to generate QR code.` | Upstream QR generator failed (e.g. Pay by Square API outage). Retry; the request is safe to repeat. |

# Simple payment

Simple example how to make simple payment

1. Generate api key and secret
   * You can do it in backoffice([Sandbox](https://sandbox.payout.one/developers/keys/new) or [Production](https://app.payout.one/developers/keys/new)) after you have already created account.
   * It's required to add notify url before api key is generated. This url will be used for sending webhook notifications (POST HTTP Requests) about state of checkouts and other events.

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
3. Create checkout with details from your order. It's POST HTTP call with JSON body. Call have to contain also Authorization header with Bearer token from previous step
   ```bash
   curl --location --request POST 'https://sandbox.payout.one/api/v1/checkouts' \
   --header 'Content-Type: application/json' \
   --header 'Authorization: Bearer SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgA.WnBcvEfet2jJr4OPF984RGTKu-8HcHPQKJitk_kJKiU' \
   --header 'Accept: application/json' \
   --header 'Idempotency-Key: 74775d02-745f-4198-cf3c-be9f1971dabe' \
   --data-raw '{
       "amount": "300",
       "currency": "EUR",
       "iban": "SK5511000000002611391222",
       "customer": {
           "first_name": "John",
           "last_name": "Doe",
           "email": "john.doe@payout.one",
           "phone": "123-4567890"
       },
       "billing_address": {
           "name": "John Doe",
           "address_line_1": "Billing Address Line 1",
           "address_line_2": "Billing Address Line 2",
           "city": "Billington",
           "postal_code": "BL92883",
           "country_code": "GB"
       },
       "shipping_address": {
           "name": "John Doe",
           "address_line_1": "Shipping Address Line 1",
           "address_line_2": "Shipping Address Line 2",
           "city": "Shippington",
           "postal_code": "W153KF",
           "country_code": "GB"
       },
       "products": [
           {
               "name": "Product 1",
               "unit_price": 100,
               "quantity": 3
           }
       ],
       "external_id": "74775d02-745f-4198-cf3c-be9f1971dabe",
       "nonce": "1474e979-9f64-012a-6d8a-f00957d4a4a0",
       "metadata": {
           "note": "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been."
       },
       "redirect_url": "https://some-eshop.local/merchant_redirect_url",
       "signature": "ef30790284ffb097e7e4b0d1162db605f97f52c59f0cfc877870bde4e61f7d77"
   }'
   ```
   > [!NOTE]
   > Amount is in cents (EUR), so 3 EUR is 300. It's same for other currencies, for example 300 CZK is 30000.

   Signature is generated from string with this pattern:
   ```
   amount|currency|external_id|nonce|client_secret
   ```
   For this specific request:
   ```
   300|EUR|74775d02-745f-4198-cf3c-be9f1971dabe|1474e979-9f64-012a-6d8a-f00957d4a4a0|q3dpHpYtDrH-KmGD4HMn5OTEx6IsZPBokQ8CqMONWqMSEePWy9bXd3Ua3KvO7f6C
   ```
   This string is hashed with SHA256 and encoded with Base16 to this form:
   ```
   ef30790284ffb097e7e4b0d1162db605f97f52c59f0cfc877870bde4e61f7d77
   ```
   > [!NOTE]
   > Some algorithms implementations generate output in UPPERCASE form so please change all characters into lowercase form.

4. Verify response from created checkout call
   Response body from previous step contain `signature` attribute which has to be verified to be sure answer is from Payout systems. Process is similar like for signature for creating checkout. Signature has to be generated and compared with signature from response, they have to be same.
   ```json
   {
       "amount": 300,
       "billing_address": {
           "address_line_1": "Billing Address Line 1",
           "address_line_2": "Billing Address Line 2",
           "city": "Billington",
           "country_code": "GB",
           "name": "John Doe",
           "postal_code": "BL92883"
       },
       "checkout_url": "https://sandbox.payout.one/checkouts/U0ZNeU5UWS5nMmdEZEFBQUFBSmtBQU5oY0dsaElXUUFBbWxrWWdBQ0tJZHVCZ0JtS1hrTGZnRmlBQUZSZ0EuR2xYdDlsZjY4NDNIY2xaUXFXTFBGdHFETWZDNmw3SXViOG1wM0VXYi1nOA",
       "currency": "EUR",
       "customer": {
           "email": "john.doe@payout.one",
           "first_name": "John",
           "last_name": "Doe",
           "name": "John Doe",
           "note": null,
           "phone": "123-4567890"
       },
       "external_id": "74775d02-745f-4198-cf3c-be9f1971dabe",
       "id": 141447,
       "idempotency_key": "74775d02-745f-4198-cf3c-be9f1971dabe",
       "metadata": {
           "note": "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been."
       },
       "nonce": "WWdVaGk4d3ZqeHFOTjM4Qw",
       "object": "checkout",
       "payment": null,
       "products": [
           {
               "name": "Product 1",
               "quantity": 3,
               "unit_price": 100
           }
       ],
       "redirect_url": "https://some-eshop.local/merchant_redirect_url",
       "shipping_address": {
           "address_line_1": "Shipping Address Line 1",
           "address_line_2": "Shipping Address Line 2",
           "city": "Shippington",
           "country_code": "GB",
           "name": "John Doe",
           "postal_code": "W153KF"
       },
       "signature": "c1bbd464676a186efb320febbb1d8d7f24fbf96783ce7e64f0cfe6b679ff14af",
       "status": "processing"
   }
   ```
   Signature is generated from string with this pattern:
   ```
   amount|currency|external_id|nonce|client_secret
   ```
   For this specific response:
   ```
   300|EUR|74775d02-745f-4198-cf3c-be9f1971dabe|WWdVaGk4d3ZqeHFOTjM4Qw|q3dpHpYtDrH-KmGD4HMn5OTEx6IsZPBokQ8CqMONWqMSEePWy9bXd3Ua3KvO7f6C
   ```
   This string is hashed with SHA256 and encoded with Base16 to this form:
   ```
   c1bbd464676a186efb320febbb1d8d7f24fbf96783ce7e64f0cfe6b679ff14af
   ```
   > [!NOTE]
   > Some algorithms implementations generate output in UPPERCASE form so please change all characters into lowercase form.

5. Redirect customer to redirect url from url from `checkout_url` attribute from response.
6. Customer is redirected to redirect url after process of payment is successful or failed. Redirect url is defined in step with creating checkout as `redirect_url` attribute.
7. Information about state of checkout / customer payment is not delivered with redirection but asynchronously with Webhook POST callback. This callback is sent to notify url. It's required to verify signature to verify that call is coming from Payout System. Signature has to be generated manually and compared with signature from `signature` attribute from webhooks. They have to be exactly the same.
   Webhook with successful checkout:
   ```json
   {
       "data":
       {
           "id": 141209,
           "amount": 300,
           "object": "checkout",
           "status": "succeeded",
           "payment":
           {
               "fee": 8,
               "net": 292,
               "object": "payment",
               "status": "successful",
               "created_at": 1635412755,
               "failure_reason": "",
               "payment_method": "PayU"
           },
           "currency": "EUR",
           "customer":
           {
               "email": "john.doe@payout.one",
               "first_name": "John",
               "last_name": "Doe"
           },
           "metadata": null,
           "card_mask": "401200******1120",
           "external_id": "1472",
           "redirect_url": "https://some-eshop.local/merchant_redirect_url"
       },
       "type": "checkout.succeeded",
       "nonce": "QjJqWEtiVDBNSmMyTm11dg",
       "object": "webhook",
       "signature": "f3b8264f42930eff215c6570f4bcdd50bcedcaf3c6da8ccfd301c6de41f36607",
       "external_id": "1472"
   }
   ```
   Signature is generated from string with this pattern:
   ```
   external_id|type|nonce|client_secret
   ```
   For this specific request:
   ```
   74775d02-745f-4198-cf3c-be9f1971dabe|checkout.succeeded|QjJqWEtiVDBNSmMyTm11dg|q3dpHpYtDrH-KmGD4HMn5OTEx6IsZPBokQ8CqMONWqMSEePWy9bXd3Ua3KvO7f6C
   ```
   This string is hashed with SHA256 and encoded with Base16 to this form:
   ```
   f3b8264f42930eff215c6570f4bcdd50bcedcaf3c6da8ccfd301c6de41f36607
   ```
   > [!NOTE]
   > Some algorithms implementations generate output in UPPERCASE form so please change all characters into lowercase form.
8. Merchant's order can be marked as paid after webhook type "checkout.succeeded" is received and verified.

**Test cards**

| Number | Month | Year | CVV | 3DS result | Behavior |
| --- | --- | --- | --- | --- | --- |
| 4245757666349685 | 12 |	29 | 123 | challenge required	|	Positive authorization
| 5150030090350186 | 12	| 29 | 123 | 3DS Method required and then successful frictionless	|	Positive authorization
| 4012001037141120 | 12	| 29 | 123 | 3DS Method and challenge required	|	Positive authorization
| 5100052384536834 | 12	| 29 | 123 | challenge params if sdk object sent in OrderCreateRequest	|	Positive authorization
| 5100052384536818 | 02	| 32 | 123 | challenge required / if no 3DS is used, returns soft decline (SSD)	|	Positive authorization
| 5100052384536826 | 12	| 29 | 123 | frictionless positive authentication	|	Positive authorization
| 5521455186577727 | 12	| 29 | 123 | frictionless negative authentication	|	no authorization (authentication fails)

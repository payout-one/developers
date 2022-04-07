# Recurrent payment

1. Generate api key and secret
   * You can do it in backoffice ([Sandbox](https://sandbox.payout.one/developers/keys/new) or [Production](https://app.payout.one/developers/keys/new)) after you have already created account.
   * It's required to add notify url before api key is generated. This url will be used for sending webhook notifications (POST HTTP Requests) about state of checkouts and other events.

2. Make authorization call to get Bearer token

   ```bash
   curl --location --request POST 'https://test.payout.one/api/v1/authorize' \
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
3. Create checkout with details from your order as in Simple Payment example but with special parameter _mode_ and value **store_card**. It's POST HTTP call with JSON body. Call have to contain also Authorization header with Bearer token from previous step
   ```bash
   curl --location --request POST 'https://app.payout.one/api/v1/checkouts' \
   --header 'Content-Type: application/json' \
   --header 'Authorization: Bearer SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgA.WnBcvEfet2jJr4OPF984RGTKu-8HcHPQKJitk_kJKiU' \
   --header 'Accept: application/json' \
   --header 'Idempotency-Key: 74775d02-745f-4198-cf3c-be9f1971dabe' \
   --data-raw '{
       "amount": "300",
       "currency": "EUR",
       "iban": "SK5511000000002611391222",
       "mode": "store_card",
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

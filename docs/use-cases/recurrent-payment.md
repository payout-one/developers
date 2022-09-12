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

4. After successful payment there are sent 2 type of webhooks:
    * **checkout.succeeded** - contains card_mask so you can save it
    ```json
     {
      "data": {
        "id": 32222,
        "amount": 300,
        "object": "checkout",
        "status": "succeeded",
        "payment": {
          "fee": 35,
          "net": 1535,
          "object": "payment",
          "status": "successful",
          "created_at": 1662716838,
          "failure_reason": "",
          "payment_method": "PayU"
        },
        "currency": "EUR",
        "customer": {
          "email": "john.doe@payout.one",
          "last_name": "John",
          "first_name": "Doe",
          "card_number_masked": ""
        },
        "metadata": null,
        "external_id": "9207dd00-d8f1-475a-a317-1067b487fdd6",
        "redirect_url": "https://example.com"
      },
      "type": "checkout.succeeded",
      "nonce": "UzhER2lFOFZCNkNQVmNuNQ",
      "object": "webhook",
      "signature": "b95494dd09183b7cbca40f356d7s4f567sdf765sdf79e1f4a95e936",
      "external_id": "9207dd00-d8f1-475a-a317-1067b487fdd6"
    }
    ``` 
    * **payu_token.created** - contains token for recurrent payments
    ```json
     {
      "data": {
        "object": "payu_token",
        "card_mask": "444405******1111",
        "checkout_id": 32222,
        "token_value": "QTEyOEdDTQ.IuWl453sdfsdfsdf8DJRuXdJetbTXA8-vRQWxJYm6zkXB5O0Vxuok019V8.ool6VIXh-u-9dy_C._n2ioCHjys3teQ8WmEM5W08ESwwXTjT0mpLdiLZdLwhJjhbtTW33HdKbNAZFfdgdfg4erggre345a-e9KamwQzXW0_lK8vw.YTYfmlJ65UkVSMa9uXhgLw"
      },
      "type": "payu_token.created",
      "nonce": "UTdsUHJBMnhIaklnS254Ng",
      "object": "webhook",
      "signature": "44444cba7039ab5d6ca048b46016f225db66cd29711fbf9023e0e6c27cfc10f1",
      "external_id": "9207dd00-d8f1-475a-a317-1067b487fdd6"
    }
    ```

5. With received recurrent token from webhook you can now make recurrent payment with saved card. It's basically identical as previous request for checkout creation. You have to change checkout parameter _mode_ to value **recurrent** and add additional required parameter recurrent_token with value from payu_token.created webhook.

6. After successful recurrent payment there is sent **checkout.succeeded** webhook.

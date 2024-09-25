# Store Card

1. Generate API key and secret
   * You can do this in the backoffice ([Sandbox](https://sandbox.payout.one/developers/keys/new) or [Production](https://app.payout.one/developers/keys/new)) after you have already created an account.
   * It's required to add a notify URL before the API key is generated. This URL will be used for sending webhook notifications (POST HTTP Requests) about the state of checkouts and other events.

2. Make an authorization call to get a Bearer token

   ```bash
   curl --location --request POST 'https://test.payout.one/api/v1/authorize' \
   --header 'Content-Type: application/json' \
   --header 'Accept: application/json' \
   --data-raw '{
    "client_id": "DC995618-7ED8-4070-9DA0-48B6F86551C3",
    "client_secret": "q3dpHpYtDrH-KmGD4HMn5OTEx6IsZPBokQ8CqMONWqMSEePWy9bXd3Ua3KvO7f6C"
   }'
   ```
   The response of this call looks like this:
   ```json
   {
    "token": "SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgWnBcvEfet1jIr9OPF984RGTKu-8HcHPQKJitk_kJKiU",
    "valid_for": 6000
   }
   ```
3. Create a checkout with details from your order as in the Simple Payment example, but with special parameters _mode_ with value **store_card** and _recurring_ with value **false**. It's a POST HTTP call with a JSON body. The call must also contain an Authorization header with the Bearer token from the previous step
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
       "recurring": false,
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
   > Amount is in cents (EUR), so 3 EUR is 300. It's the same for other currencies; for example, 300 CZK is 30000.

   The signature is generated from a string with this pattern:
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
   > Some algorithm implementations generate output in UPPERCASE form, so please change all characters to lowercase.

4. After a successful payment, two types of webhooks are sent:
    * **checkout.succeeded**
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
    * **payu_token.created** - contains card_mask and token for stored card.
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

5. With the received card token from the webhook, you can now make a payment with the saved card. It's basically identical to the previous request for checkout creation. You just have to change checkout _mode_ to **card_on_file** and add the checkout parameter **card_token** with the value of the received token from the webhook payu_token.created.
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
       "mode": "card_on_file",
       "card_token": "QTEyOEdDTQ.IuWl453sdfsdfsdf8DJRuXdJetbTXA8-vRQWxJYm6zkXB5O0Vxuok019V8.ool6VIXh-u-9dy_C._n2ioCHjys3teQ8WmEM5W08ESwwXTjT0mpLdiLZdLwhJjhbtTW33HdKbNAZFfdgdfg4erggre345a-e9KamwQzXW0_lK8vw.YTYfmlJ65UkVSMa9uXhgLw",
       "recurring": false,
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

6. Based on the amount of the payments with stored cards, it's possible that payment will be processed without 3D Secure, but it's not guaranteed and there is a higher probability that 3D Secure will be required. Therefore, it's necessary to redirect the customer to our checkout page where the payment can be confirmed.

7. After a successful payment, a **checkout.succeeded** webhook is sent.

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

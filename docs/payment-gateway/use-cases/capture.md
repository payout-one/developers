# Capture & Cancel payment

## Capture

In the case of card payments, it is possible to authorize a certain order amount and capture full or only a portion of the funds deposited. This can be useful when some of the purchased items are unavailable or when the charge for renting a vehicle exceeds the actual amount to be paid.

This feature needs to be enabled for your specific account, therefore if you plan to use it contact our support please.

1. Generate api key and secret
   * You can do it in backoffice ([Sandbox](https://sandbox.payout.one/developers/keys/new) or [Production](https://app.payout.one/developers/keys/new)) after you have already created account.
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
3. Create checkout with amount you want to authorize on card similarly as in Simple Payment example but with special parameter _mode_ for checkout and value **pre_authorization**. It's POST HTTP call with JSON body. Call have to contain also Authorization header with Bearer token from previous step
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
       "mode": "pre_authorization",
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

4. After successful payment, webhook of type **checkout.pre_authorized** is sent to your server indicating successful authorization of amount on card :
    * **checkout.pre_authorized**
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
      "type": "checkout.captured",
      "nonce": "UzhER2lFOFZCNkNQVmNuNQ",
      "object": "webhook",
      "signature": "b95494dd09183b7cbca40f356d7s4f567sdf765sdf79e1f4a95e936",
      "external_id": "9207dd00-d8f1-475a-a317-1067b487fdd6"
    }
    ```

5. Now it's possible to do full capture meaning charging customer's card for whole amount which was pre-authorized or you can do partial capture.

6. Full capture example (note ID of the checkout in the request path and sending empty body):
```bash
   curl --location --request POST 'https://sandbox.payout.one/api/v1/checkouts/32222/capture' \
   --header 'Content-Type: application/json' \
   --header 'Authorization: Bearer SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgA.WnBcvEfet2jJr4OPF984RGTKu-8HcHPQKJitk_kJKiU' \
   --header 'Accept: application/json' \
   --header 'Idempotency-Key: 74775d02-745f-4198-cf3c-be9f1971dabe' \
   --data-raw '{}'
   ```

6. Partial capture example (note ID of the checkout in the request path and amount param in the body):
```bash
   curl --location --request POST 'https://sandbox.payout.one/api/v1/checkouts/32222/capture' \
   --header 'Content-Type: application/json' \
   --header 'Authorization: Bearer SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgA.WnBcvEfet2jJr4OPF984RGTKu-8HcHPQKJitk_kJKiU' \
   --header 'Accept: application/json' \
   --header 'Idempotency-Key: 74775d02-745f-4198-cf3c-be9f1971dabe' \
   --data-raw '{
    "amount": 150
   }'
   ```

8. After successful capture of funds there is sent **checkout.captured** webhook.

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


## Cancel
> It's possible to cancel checkout if a product or service is not delivered.
>
> Only checkouts for which **checkout.captured** webhook was not triggered can be cancelled.

To cancel pre-authorized checkout and proceed with a refund to the Payer's account, call the endpoint `/api/v1/checkouts/{checkoutId}` using the DELETE method.
```bash
   curl --location --request DELETE 'https://sandbox.payout.one/api/v1/checkouts/32222' \
   --header 'Content-Type: application/json' \
   --header 'Authorization: Bearer SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgA.WnBcvEfet2jJr4OPF984RGTKu-8HcHPQKJitk_kJKiU' \
   --header 'Accept: application/json' \
   --header 'Idempotency-Key: 74775d02-745f-4198-cf3c-be9f1971dabe'
   ```

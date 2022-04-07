# Refund

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
   
3. Create request with details from checkout. It's POST HTTP call with JSON body. Call have to contain also Authorization header with Bearer token from previous step
   ```bash
   curl --location --request POST 'https://app.payout.one/api/v1/refunds' \
   --header 'Content-Type: application/json' \
   --header 'Authorization: Bearer SFMyNTY.g2gDYSFuBgCaSXELfgFiAAFRgA.WnBcvEfet2jJr4OPF984RGTKu-8HcHPQKJitk_kJKiU' \
   --header 'Accept: application/json' \
   --header 'Idempotency-Key: 74775d02-745f-4198-cf3c-be9f1971dabe' \
   --data-raw '{
	     "amount": 100,
	     "checkout_id": 141209, 
	     "iban": "SK5511000000002611391222",
	     "statement_descriptor": "Description on customer statement",
	     "nonce": "1474e979-9f64-012a-6d8a-f00957d4a4a0",
	     "signature": "ef30790284ffb097e7e4b0d1162db605f97f52c59f0cfc877870bde4e61f7d77" 
   }'
   ```
   Amount parameter is optional.
   ```
   ```
   Signature is generated from string with this pattern:
   ```
   amount|currency|external_id|iban|nonce|client_secret
   ```
   This string is hashed with SHA256 and encoded with Base16 to this form:
   ```
   ef30790284ffb097e7e4b0d1162db605f97f52c59f0cfc877870bde4e61f7d77
   ```
   > [!NOTE]
   > Some algorithms implementations generate output in UPPERCASE form so please change all characters into lowercase form.  

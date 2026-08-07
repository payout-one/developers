# Payout Banklink API

## List Accounts

`POST /accounts`

Retrieve current user connected accounts

### Example

```bash
curl -X POST https://app.payout.one/accounts \
  -H "Authorization: Bearer $TOKEN"
```


## Account Balances

`POST /accounts/balance`

Retrieve current user account balance directly from bank

### Example

```bash
curl -X POST https://app.payout.one/accounts/balance \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "bank": "vub",
       "iban": "nostrud incididunt aute occaecat"
     }'
```


## Account Information

`POST /accounts/information`

Retrieve current user account information directly from bank

### Example

```bash
curl -X POST https://app.payout.one/accounts/information \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "bank": "vub",
       "iban": "nostrud incididunt aute occaecat"
     }'
```


## Verify IBAN

`POST /accounts/verify-iban`

Verify that current user has access to account with specified IBAN

### Example

```bash
curl -X POST https://app.payout.one/accounts/verify-iban \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "bank": "vub",
       "iban": "nostrud incididunt aute occaecat"
     }'
```


## Account Details

`POST /api/v1/accounts/details`

### Example

```bash
curl -X POST https://app.payout.one/api/v1/accounts/details \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "bank": "vub",
       "iban": "SK0511000000002600000054"
     }'
```


## Consent Accounts

`POST /api/v1/provider/accounts`

### Example

```bash
curl -X POST https://app.payout.one/api/v1/provider/accounts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "consent_id": 123
     }'
```


## Payment initialisation

`POST /payments/{integration}/{payment_product}`

### Example

```bash
curl -X POST https://app.payout.one/payments/{integration}/{payment_product} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "endToEndIndentification": "/VS1/SS2/KS3",
       "creditorAgent": "GIBASKBX",
       "creditorName": "John Doe",
       "debtorName": "Test Testovic",
       "remittanceInformationUnstructured": "Testing",
       "debtorAccount": {
         "iban": "SK5409000000005037706253"
       },
       "creditorAccount": {
         "iban": "SK0511000000002600000054"
       },
       "instructedAmount": {
         "amount": "1.00",
         "currency": "EUR"
       }
     }'
```


## Payment status

`GET /payments/{payment_id}/status`

### Example

```bash
curl -X GET https://app.payout.one/payments/{payment_id}/status \
  -H "Authorization: Bearer $TOKEN"
```


## List Integrations

`GET /api/v1/integrations`

### Example

```bash
curl -X GET https://app.payout.one/api/v1/integrations \
  -H "Authorization: Bearer $TOKEN"
```


## Create Verification

`POST /api/v1/verifications`

### Example

```bash
curl -X POST https://app.payout.one/api/v1/verifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "iban": "CZ4108000000000782553098",
       "first_name": "Jir\u00ed",
       "last_name": "Spokojen\u00fd"
     }'
```


## Get Verification Status

`GET /api/v1/verifications/{verification_id}`

### Example

```bash
curl -X GET https://app.payout.one/api/v1/verifications/{verification_id} \
  -H "Authorization: Bearer $TOKEN"
```


## /transactions

`POST /transactions`

Retrieve current user transactions directly from bank

### Example

```bash
curl -X POST https://app.payout.one/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "bank": "vub",
       "iban": "nostrud incididunt aute occaecat"
     }'
```


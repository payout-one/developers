# Payout OpenBanking PSD2 API

## enrol

`POST /api/psd2/v1/enrol`

Enrol new client. This call will return new client credentials, which will be disabled. Client TPP then will by contacted via first contact email and process will be finished manualy. This request must by done using PSD2 certificate.

# Request
|Name|Type|Description|
|----|----|-----------|
| licenseNumber | string | PSD2 license number of TPP |
| clientName | string | Client name of TPP |
| logoUri | string | URL to publicli accesible logo of TPP |
| scopes | string[] | List of scopes which TPP will require |
| contacts | string[] | List of emails which can by used to contact TPP, must be at least one |
| redirectUris | string[] | Redirect URL's which TPP will use |
| certificate | string | Base64 encoded PSD2 certificate |

# Response
| Name | Type |
| ---- | ---- |
| licenseNumber | string |
| clientId | string |
| clientSecret | string |
| clientName | string |
| logoUri | string |
| scopes | string[] |
| contacts | string[] |
| redirectUris | string[] |

### Example

```bash
curl -X POST https://app.payout.one/api/psd2/v1/enrol \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "licenseNumber": "12345",
       "clientName": "Testovic Postman, s.r.o",
       "certificate": "MIIEkzCCA3ugAwIBAgIJAK0JKpzx6C9mMA0GCSqGSIb3DQEBCwUAMIGSMQswCQYDVQQGEwJTSzEPMA0GA1UECAwGWmlsaW5hMQ8wDQYDVQQHDAZaaWxpbmExFzAVBgNVBAoMDlBheW91dCwgcy5yLm8uMQswCQYDVQQLDAJJVDESMBAGA1UEAwwJbG9jYWxob3N0MScwJQYJKoZIhvcNAQkBFhhtYXJ0aW4uY2VybmFrQHBheW91dC5vbmUwHhcNMjAxMjE0MDYyNTE1WhcNMjIwNDI4MDYyNTE1WjCBkjELMAkGA1UEBhMCU0sxDzANBgNVBAgMBlppbGluYTEPMA0GA1UEBwwGWmlsaW5hMRcwFQYDVQQKDA5QYXlvdXQsIHMuci5vLjELMAkGA1UECwwCSVQxJzAlBgkqhkiG9w0BCQEWGG1hcnRpbi5jZXJuYWtAcGF5b3V0Lm9uZTESMBAGA1UEAwwJbG9jYWxob3N0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzInaKn0XdvTSpSNYzbZI1A4gky0zoyBggz5Q7sGHokZyiriCRYxHw91jkSskp0RU7xV41zf651+z3FtB8U/vUmsNZfX1eJ/MaSPfnohATQVzC+GxLtO89gGlKLD+ihMfXMfQf+yt76eA/bslvGp36EYhW1ou2+DjRzae4eyoFEUTdGoAtXArLslrK01VJdR9yxUYRDtm5S+hhAboJzyNry/I5I15fZkf8t3jJeSzBNLwuW4IP4nu18DdwmOnw63yRlHUpgYQzqvv/+xgf3HcgqUkORq2HXbAHaEYe1S5P/6kvupZmz+vbHbx3Bvsbt9mkgg/OpYIU2WfJ9NLcLUT5wIDAQABo4HpMIHmMIGxBgNVHSMEgakwgaahgZikgZUwgZIxCzAJBgNVBAYTAlNLMQ8wDQYDVQQIDAZaaWxpbmExDzANBgNVBAcMBlppbGluYTEXMBUGA1UECgwOUGF5b3V0LCBzLnIuby4xCzAJBgNVBAsMAklUMRIwEAYDVQQDDAlsb2NhbGhvc3QxJzAlBgkqhkiG9w0BCQEWGG1hcnRpbi5jZXJuYWtAcGF5b3V0Lm9uZYIJAMidpY+XJANIMAkGA1UdEwQCMAAwCwYDVR0PBAQDAgTwMBgGA1UdEQQRMA+CDWNsaWVudC5wYXlvdXQwDQYJKoZIhvcNAQELBQADggEBAJwuqXE21bA5kkcZYRYw9rhXzo/EMhCqUxsprVEk990536X1YBIBUUJk4cI1TjReOZAi1cMG2qpk46Ex4vXKyx8jbcPXchf30B9shaxZETahJ2I8w8J1hBMnSY3gfv8mwooRrjmZJsd8+zIVf/5L+vdZgqHru53huOSEoQLJKkgAqX3qDczqoaFV7Rx5oVI77P9sXcIN39Rr2rlh5P87k0yxmEYecPq/Cd98NJBRTCE94aPOGyysfPvZ6gAcXPcui47PZLeTeIk+SsIBPHFhSe7RuFa4vAj6CY//t14XmCyzcHCW05W32+6Zn97CFKwEazQqdUuhalHkn3fyZhmy5IY=",
       "scopes": [
         "AISP"
       ],
       "contacts": [
         "test@example.com"
       ],
       "redirectUris": [
         "https://oauth.pstmn.io/v1/browser-callback"
       ]
     }'
```


## list accounts

`GET /api/psd2/v1/accounts`

List all accounts of current user

# Response
| Name | Type | Description |
| ---- | ---- | ----------- |
| identification | Identification | | 
| name | string | Name of account |
| productName | string | Name of product which is represented by this account |
| type | string | Type of account, staticalli "CACC" |
| baseCurrency| string | Currency code of account according to ISO 4217 - 3 capital letters, statically "EUR" |
| servicer |  string | Name of service responsible for this account |
| consent | string | Scopes acquired for this account |

## Identification
| Name | Type | Description |
| ---- | ---- | ----------- |
| identifier | string | Unique identification |

### Example

```bash
curl -X GET https://app.payout.one/api/psd2/v1/accounts \
  -H "Authorization: Bearer $TOKEN"
```


## account info

`POST /api/psd2/v1/accounts/information`

Retrieve detailed info about user account

# Request
| Name | Type | Description | Example |
| ---- | ---- | ----------- | ------- |
| identifier | string | Identificator of account | "xHiZzdwcxMOu" |

# Response
| Name | Type |
| ---- | ---- |
| account | Account |
| balances | Balance[] |

## Account
| Name | Type | Description |
| ---- | ---- | ----------- | 
| name | string | Name of account |
| productName | Name of product of which instance is this account |
| baseCurrency | string | Basic currency of thsi account in ISO 4217 |
| type | string | ISO 20022 - Cash Account Type Code |

## Balance 
| Name | Type | Description |
| ---- | ---- | ----------- |
| name | string | Name of account | 
| typeCodeOrProprietary | string | Staticali "ITAV" |
| amount | Amount | |
| creditDebitIndicator | CreditDebitIndicator | |

### Example

```bash
curl -X POST https://app.payout.one/api/psd2/v1/accounts/information \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "identifier": "xHiZzdwcxMOu"
     }'
```


## list transactions

`POST /api/psd2/v1/accounts/transactions`

List all transactions for user or account

## Transaction
| Name | Type | Description | Example |
| ---- | ---- | ----------- | ------- |
| amount | Amount | Value of transaction | |
| creditDebitIndicator | "CRDT" \| "DBIT" | Indicates if this transaction is credit or debit transaction | "CRDT" |
| reversalIndicator | boolean | Indicates if this transaction is rollback of some previous transaction | true |
| status | "INFO" \| "BOOKED" | Indicates whatever transaction was executed ("INFO") or is pending ("BOOKED") | "INFO" |
| bookingDate | string | | "2008-03-20" |
| valueDate | stirng | | "2008-03-20" |
| bankTransactionCode | enum | `TODO` | |
| transactionDetails | TransactionDetails | | |
| additionalTransactionInformation | string | Aditional technical information about transaction | |

## Amount
Represent value with currency

| Name | Type | Description | Example |
| ---- | ---- | ----------- | ------- |
| value | number | Number rounded to 2 decimals representing amount of money | 0.12 |
| currency | string | Currency code according to ISO 4217 - 3 capital letters | "EUR" |

## TransactionDetails
| Name | Type | Description | Example |
| ---- | ---- | ----------- | ------- |
| references | References | Attribute that identify transaction | |
| relatedParties | RelatedParties | Parties between which transaction is executed | | 
| relatedDates | RelatedDates | Important dates from transaction processing | |

## References
| Name | Type | Description | Example |
| ---- | ---- | ----------- | ------- |
| accountServicerReference | string | Internal service provider transaction reference | | 
| endToEndIdentification | string | Client assigned transaction reference | |

## RelatedParties
| Name | Type | Description | Example |
| ---- | ---- | ----------- | ------- |
| debtor | Party | | | 
| debtorAccount | PartyIdentification | |
| creditor | Party | | |
| creditorAccount | PartyIdentification | |

## Party
| Name | Type | Description |
| ---- | ---- | ------- |
| name | string | Name of the party |

## PartyAccount 
| Name | Type | Description |
| ---- | ---- | ----------- |
| identification | string | Globaly identifies party, can by internal identificator, IBAN, etc. |

### Request body

- `identifier` — string · Identifier of account for which to return transactions · e.g. Wh_qu9uJ0XoN
- `dateFrom` — string · Limit results to by never that specified date · e.g. 2020-12-20
- `dateTo` — string · Limit results to by older than specified date · e.g. 2020-08-21
- `status` — string · false
- `pageSize` — number · Number of results to return · e.g. 20.0
- `page` — number · Current page in pagination · e.g. 4.0

### Response

- `pageCount` — number · Total number of pages after filtering · e.g. 3.0
- `transactions` — string · List of returned transactions

### Example

```bash
curl -X POST https://app.payout.one/api/psd2/v1/accounts/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "page": 2,
       "identifier": "xHiZzdwcxMOu"
     }'
```


## standard sba payment

`POST /api/psd2/v1/payments/standard/sba`

Initialize payment using json format

# Request
| Name | Type | Required | Description | Example |
| ---- | ---- | -------- | ----------- | ------- |
| instructionIdentification | string | true | Client assigned instruction identification | "aff52ratg5ageh53" |
| debtor | Debtor | true | | |
| creditor | Creditor | true | | | 
| instructedAmount | Amount | true | | | 
| endToEndIdentification | string | false | | | 
| remittanceInformation | string | false | | |

## Debtor
| Name | Type | Description |
| ---- | ---- | ----------- |
| identifier | string | Debtor identifier, mostil account identifier |

## Creditor
| Name | Type | Description |
| ---- | ---- | ----------- |
| name | string | Full name or company name of creditor |
| iban | string | |
| email | string | |

## Amount 
| Name | Type | Description |
| ---- | ---- | ----------- |
| value | number | Number with two decimals representing money amount |
| currency | string | Currency code according to ISO 4217 |

# Response
| Name | Type | Description | Example |
| ---- | ---- | ----------- | ------- |
| orderId | string | | |
| status | string | | |
| statusDatetime | string | Date and time when status was read | "2020-12-09 23:27:30.697662Z"|

### Example

```bash
curl -X POST https://app.payout.one/api/psd2/v1/payments/standard/sba \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "instructionIdentification": "some-random-string",
       "debtor": {
         "identifier": "xHiZzdwcxMOu"
       },
       "creditor": {
         "name": "Jozko Mrkvicka",
         "iban": "creditor_iban",
         "email": "jozko.mrkvicka@pompo.po"
       },
       "instructedAmount": {
         "value": 1.0,
         "currency": "EUR"
       }
     }'
```


## submit payment

`POST /api/psd2/v1/payments/submission`

Submit initialized payment for processing. This request is done only access token that can be retrieved using `authorization_code` oauth2 mathod to special endpoint xxxx/:order_id and requires scope `PISPSUBMIT`.

### Example

```bash
curl -X POST https://app.payout.one/api/psd2/v1/payments/submission \
  -H "Authorization: Bearer $TOKEN"
```


## order status

`GET /api/psd2/v1/payments/{ORDER_ID}/status`

Return actual status of the order

### Example

```bash
curl -X GET https://app.payout.one/api/psd2/v1/payments/{ORDER_ID}/status \
  -H "Authorization: Bearer $TOKEN"
```


## balance check

`POST /api/psd2/v1/accounts/balanceCheck`

Check if account has enought resources to fullfill specified request

| Name | Type | Description |
| ---- | ---- | ----------- |
| instructionIdentification | string | Technial payment identificator generated by PIISP |
| creationDateTime | string | The date and time in RFC3339 format at which a particular action has been requested or executed. |
| identifier | string | Payout account unique identificator |
| amount | Amount | |

## Amount
| Name | Type | Description |
| ---- | ---- | ----------- |
| amount | number | Numeric value of the amount as a fractional number. |
| currency | string | Alphabetic codes from ISO 4712. |

# Response 
| Name | Type | Description |
| ---- | ---- | ----------- |
| response | string | Either "APPR" or "DECL" |
| dateTime | string | The date and time in RFC3339 format at which a particular action has been requested or executed. |

### Example

```bash
curl -X POST https://app.payout.one/api/psd2/v1/accounts/balanceCheck \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "instructionIdentification": "What-Ever",
       "identifier": "xHiZzdwcxMOu",
       "amount": {
         "amount": 6000,
         "currency": "EUR"
       }
     }'
```


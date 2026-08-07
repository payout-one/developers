# Payout Intel API

## Authorize (receive API token)

`POST /api/v1/authorize`

### Example

```bash
curl -X POST https://app.payout.one/api/v1/authorize \
  -H "Authorization: Bearer $TOKEN"
```


## Show AML limit in given country, in specified currency

`GET /api/v1/intel/limits`

This request returns limit in given currency in specified country.

Will return error if invalid `check_type` is given.

| Name | Type | Description|
| ------ | ------ | ------ |
| `currency` | string | ISO 3 currency code |
| `country` | string | ISO 2 country code |
| `check_type` | string | Check type can be <"AML4", "AML5"> |

### Example

```bash
curl -X GET https://app.payout.one/api/v1/intel/limits \
  -H "Authorization: Bearer $TOKEN"
```


## Search Customer Intel

`POST /api/v1/intel`

# Request body attributes

# ID Validation states
* **valid** - ID is valid for existing person
* **not_valid** - ID is not valid
* **unknown** - it was not possible to validate ID

# AML Check states
* **found** - exact one result
* **found_many** - more results 
* **not_found** - zero results

### Request body

- `name` — string (required) · First name · e.g. Vladimir
- `surname` — string (required) · Last name/surname · e.g. Putin
- `birthdate` — string · Date in format YYYY-MM-DD · e.g. 1952-10-23
- `id` — string · ID number · e.g. DG12345
- `address` — string · Address · e.g. H. Melickovej 13, 841 05 Moskva

### Response

- `id` — string<uuid> · ID of search result
- `url` — string · URL with result details in our system · e.g. https://ie.payout.one/link_to_result_details/c4c14b99-5a8b-45da-a235-2c159785c9ck
- `valid_id` — string · Result state of ID validation · e.g. unknown
- `aml` — string · Result state of AML check · e.g. not_found

### Example

```bash
curl -X POST https://app.payout.one/api/v1/intel \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "name": "Juraj",
       "surname": "Novak",
       "birthdate": "1952-10-23",
       "id": "AB1234",
       "address": "H. Melickovej 13, 841 05 Moskva"
     }'
```


## Calculate transaction score

`POST /api/v1/intel/calculate_score`

Please, contact support support@payout.one to allow this feature

## Transaction

|Name|Type|Required|Example|Description|
|--|--|--|--|--|
| `payment_method` | PaymentMethod | `true` | payment_method | Please see PaymentMethod |
| `bank` | text | `true` | "nbs" | Name of the bank |
| `transaction_type` | TransactionType | `true` | transaction_type | Please see TransactionType |
| `date_create` | string | `true` | "2019-01-01"  | Transaction date |
| `amount` | integer | `true` | 123456 | Smallest unit of currency |
| `currency` | text | `true` | "EUR" | Currency code by [ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) |
| `ip_address` | text | `true` | "127.0.0.1" | Clients IP address |
| `source` | TransactionSource | `true` | transaction_source | Please see TransactionSource |
| `variable_symbol` | text | `true` | 1234567890 | Variable symbol |
| `reference` | text | `true` | "message for debtor" | Transaction reference |
| `threshold` | integer | `true` | 50 | The level that must be reached for transaction to be reported  |
| `category` | TransactionCategory | `true` | transaction_category | Please see TransactionCategory |
| `transaction_id` | text | `true` | `999a0915-73d4-4870-ad14-d23c1aa45be3` | Transaction ID |
| `url` | text | `true` | url | URL address of the service |
| `creditor` | Person | `true` | object | Please see Person  |
| `debtor` | Person | `true` | object | Please see Person  |
| `credit_card` | CreditCard | `true` | object | Please see CreditCard |

## Person

|Name|Type|Required|Example|Description|
|--|--|--|--|--|
| `name` | string | `true` | "John Doe" | User`s name |
| `email` | string | `true` | "example@payout.one" | Email address |
| `phone_number` | string | `true` | "+421900123456" | Phone number |
| `iban` | string | `true` | "SK3112000000198742637541" | IBAN |
| `address` | Address | `true` | object | Please see Address |

## Address

|Name|Type|Required|Example|Description|
|--|--|--|--|--|
| `line1` | string | `true` |  line1 | Address line 1 |
| `line2` | string | `true` |  line2 | Address line 2 |
| `city` | string | `true` |  city | City |
| `zip` | string | `true` |  zip | ZIP code |
| `country` | string | `true` |  country | Country code in [ISO_3166-1](https://en.wikipedia.org/wiki/ISO_3166-1) |

## CreditCard

|Name|Type|Required|Example|Description|
|--|--|--|--|--|
| `number` | string | `true` | "6666664444" | Credit card number |
| `type` | string | `true` | type | |
| `expiration_date` | string | `true` | "12/20" | Credit card`s expiration date |
| `holder_name` | string | `true` | "John Doe" | Holder`s name |
| `3d_secure` | boolean | `true` | `true` | 3D secure requested |
| `acquirer` | string | `true` | "payout" | Acquirer`s name |
| `issuer` | string | `true` | "payout" | Issuer name|

### Example

```bash
curl -X POST https://app.payout.one/api/v1/intel/calculate_score \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "creditor": {
         "name": "",
         "email": "",
         "phone_number": "",
         "iban": "SK0123",
         "address": {
           "line1": "",
           "line2": "",
           "city": "",
           "zip": "",
           "country": ""
         }
       },
       "debtor": {
         "name": "",
         "email": "",
         "phone_number": "",
         "iban": "SK0123",
         "address": {
           "line1": "",
           "line2": "",
           "city": "",
           "zip": "",
           "country": ""
         }
       },
       "credit_card": {
         "number": "",
         "type": "",
         "expiration_date": "",
         "holder_name": "",
         "3d_secure": true,
         "acquirer": "",
         "issuer": ""
       },
       "payment_method": "credit_card",
       "bank": "",
       "transaction_type": "prijat\u00e1 \u00fahrada, odoslan\u00e1 \u00fahrada, platba kartou (CC)",
       "date_cc": "",
       "date_txn": "",
       "date_create": "",
       "amount": 10500,
       "currency": "EUR",
       "ip_address": "127.0.0.1",
       "source": "banka, eshop ",
       "variable_symbol": "",
       "reference": "",
       "threshold": 75,
       "category": "banking",
       "id": "<optional-random-id>",
       "url": "",
       "user_agent": ""
     }'
```


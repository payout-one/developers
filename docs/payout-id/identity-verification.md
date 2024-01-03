# Identity verification

   > [!NOTE]
   > This API is still heavily developed and can change in next release

PayoutID also provides identity verification and AML. It uses custom endpoint which will return redirect to start user verifications. After user provides all required data, he is redirected back to client. Since we get results from some checks asynchronously, result is delivered as webhook. This api requires to retrieve access token with `verify` scope and, if also bank account details are required, `account_info` scope.

Process is as follows:

1. retrieve access token
2. retrieve redirect from verification invitation endpoint
3. redirect user to retrieve redirect uri
4. wait for webhook

Whole process can be on following diagram:

![Payout ID verification diagram](../_media/payout-id-verification.png)

Documentation for verification invitation endpoint can be found [here](https://documenter.getpostman.com/view/10478778/2s9YsFDYzn#08658c94-347c-448d-9b16-8c7cfcb0f3d0)

## Retrieving access token

You need to retrieve this token using `client credentials grant`, with required scope `verify` and optional scope `account_info` in case you want to retrieve client bank account details. [Here](https://documenter.getpostman.com/view/10478778/2s9YsFDYzn#f885ffae-52a8-47b8-86e1-decceb9fec2c) you will find documentation for access token endpoint.

## Webhook

After all required data is collected, it is send to client using webhook, webhook is also signed and client should verify signature to prevent fraudelant calls. Webhook is delivered using `POST` method. To url client provides as `notify_url` in request to create identity verification invitation.

### Attributes

Webhook will contain following attributes:

| path | type | required | example | description |
| ---- | ---- | --- | --- | --- |
| data | object | yes | - | contains all data |
| data/id | string | yes | "edf29e60-45a5-463b-b120-033e835df3ce" | identificator of invitation, should be same as in invitation create response |
| data/provided_email | string | yes | "john.doe@example.com" | email provided by user |
| data/provided_name | string | yes |  "John" | user provided first name |
| data/provided_surname | string | yes |  "Doe" | user provided last name |
| data/provided_is_sanctioned | boolean | yes |  false | user answer to question if he is on sanction list |
| data/provided_is_pep | boolean | yes |  false | user answer to question if he is politicaly exposed person |
| data/identity_verification_failed | boolean | yes | false | indicates that identity verification failed |
| data/bank_account_owner_name | string or null | yes | "John Doe" | retrieved account owner name from bank, is null in case we failed to retrieve or invitation did not requested bank account details |
| data/bank_account_requested | boolean | yes |  false | indicates that when this identity verification was created, bank account owner name retrieval was requested |
| data/bank_account_unsupported_integration | boolean | yes | false | indicates that user choosed that hi does not have account in integrated banks |
| data/bank_account_iban | string or null | yes | null | retrieved IBAN from bank, null in case user don't provide access or retrieval was not requested |
| data/document_type | string | no | "ID_CARD" | which kind of document user used to finish verification, one of [document types](#document-types) |
| data/suspicion_reasons | array of strings | no | ["FACE_SUSPECTED"] | - |
| data/client_ip | string | no | "95.103.174.26" | User system IP address |
| data/client_ip_country | string | no | "SK" | User IP address country code |
| data/client_location | string | no | - | Information about location by clients IP address |
| data/finish_time | string | no | "2023-12-07T13:16:44Z" | - |
| data/document_valid_until | string | no | "2023-12-13" | - |
| data/auto_document | string | no | - | - |
| data/overall | string | no | "APPROVED" | Finall status of verification can be one of APPROVED, SUSPECTED or DENIED |
| data/fraud_tags | array of strings | no | [] | Descrbe suspicion reasons in case overall is SUSPECTED |
| data/start_time | string | no | "2023-12-07T13:16:44Z" | - |
| data/auto_face | string | no | "FACE_MATCH" | Describe result of automatic photo face recognition |
| data/aditional_steps | - | no | - | - |
| data/document_number | string | no | "DE4878783" | Number of document of the user |
| data/platform | string | - | - | - |
| data/manual_face | string | no | "FACE_MATCH" | Result of manual examination of photos |
| data/mismatch_tags | array of strings | no | [] | List of mismatched attributes from document |
| data/manual_document | string | no | "DOC_VALIDATED" | - |
| signature | string | yes | - | Signature to verify origin of the returned data |
| nonce | string | yes | - | Used to sign data |

#### Document types

- ID_CARD
- PASSPORT
- RESIDENCE_PERMIT
- DRIVER_LICENSE
- PAN_CARD
- AADHAAR
- OTHER
- VISA
- BORDER_CROSSING
- ASYLUM
- NATIONAL_PASSPORT
- INTERNATIONAL_PASSPORT
- PROVISIONAL_DRIVER_LICENSE
- VOTER_CARD
- OLD_ID_CARD
- TRAVEL_CARD
- PHOTO_CARD
- MILITARY_CARD
- PROOF_OF_AGE_CARD
- DIPLOMATIC_ID


### Examples

Successfull and only identity verification:

``` json
{
  "data": {
    "aditional_steps": null,
    "auto_document": "DOC_VALIDATED",
    "auto_face": "FACE_MATCH",
    "bank_account_iban": null,
    "bank_account_owner_name": null,
    "bank_account_requested": false,
    "bank_account_unsupported_integration": false,
    "client_ip": "177.77.77.196",
    "client_ip_country": "LT",
    "client_location": "Kaunas, Lithuania",
    "document_number": "DE4878783",
    "document_type": "PASSPORT",
    "document_valid_until": "2024-03-09",
    "finish_time": "2023-12-07T13:16:44Z",
    "fraud_tags": [],
    "id": "ac286ff1-4e3c-41c7-ab00-127605583d36",
    "identity_verification_failed": false,
    "manual_document": "DOC_VALIDATED",
    "manual_face": "FACE_MATCH",
    "mismatch_tags": [],
    "overall": "APPROVED",
    "platform": "PC",
    "provided_email": "john.doe@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "John",
    "provided_surname": "Doe",
    "start_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": []
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "770f0ced79a63f262b12313a8ea2519188df90097c9c147c896d04df13b05b7b"
}
```

In case of failed verification this is returned

```json
{
  "data": {
    "bank_account_iban": null,
    "bank_account_owner_name": null,
    "bank_account_requested": false,
    "bank_account_unsupported_integration": false,
    "id": "ac286ff1-4e3c-41c7-ab00-127605583d36",
    "identity_verification_failed": true,
    "provided_email": "john.doe@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "John",
    "provided_surname": "Doe"
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "4253a96ed056105a1bc1472771d2db34e19f4777f4c8541d368e06ab57a1c33a"
}
```

Webhook when also account details are returned:

```json
{
  "data": {
    "aditional_steps": null,
    "auto_document": "DOC_VALIDATED",
    "auto_face": "FACE_MATCH",
    "bank_account_iban": "SK0431000000002333363431",
    "bank_account_owner_name": "John Doe",
    "bank_account_requested": true,
    "bank_account_unsupported_integration": false,
    "client_ip": "177.77.77.196",
    "client_ip_country": "LT",
    "client_location": "Kaunas, Lithuania",
    "document_number": "DE4878783",
    "document_type": "PASSPORT",
    "document_valid_until": "2024-03-09",
    "finish_time": "2023-12-07T13:16:44Z",
    "fraud_tags": [],
    "id": "86680181-dd10-49db-94ad-f45d9f75291c",
    "identity_verification_failed": false,
    "manual_document": "DOC_VALIDATED",
    "manual_face": "FACE_MATCH",
    "mismatch_tags": [],
    "overall": "APPROVED",
    "platform": "PC",
    "provided_email": "john.doe@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "John",
    "provided_surname": "Doe",
    "start_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": []
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "21991adac6f174fe3b3d7b5b978b16dcbce35e43cda89e7ee8c07ecf8c9596c5"
}
```

Webhook in case user chooses that he does not have account in any of supported banks:

``` json
{
  "data": {
    "aditional_steps": null,
    "auto_document": "DOC_VALIDATED",
    "auto_face": "FACE_MATCH",
    "bank_account_iban": null,
    "bank_account_owner_name": null,
    "bank_account_requested": true,
    "bank_account_unsupported_integration": true,
    "client_ip": "177.77.77.196",
    "client_ip_country": "LT",
    "client_location": "Kaunas, Lithuania",
    "document_number": "DE4878783",
    "document_type": "PASSPORT",
    "document_valid_until": "2024-03-09",
    "finish_time": "2023-12-07T13:16:44Z",
    "fraud_tags": [],
    "id": "f0517635-5461-4356-b41e-28ef541dcbe6",
    "identity_verification_failed": false,
    "manual_document": "DOC_VALIDATED",
    "manual_face": "FACE_MATCH",
    "mismatch_tags": [],
    "overall": "APPROVED",
    "platform": "PC",
    "provided_email": "john.doe@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "John",
    "provided_surname": "Doe",
    "start_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": []
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "5e85fec7c31e61827cc863ac7b64468099cd74871c1f7277addf8ff87fcabc4b"
}
```

### Signature

To verify signature, you need to concat all returned values from data, nonce and you client secret. These data should be separated using pipe `|`. Resulting string is then neceseary to hash using `SHA256` algorithm. Then it should be base16 encoded and all character should be downcased. For instance if I have imaginary webhook containing only 2 parameters first_name and last_name so webhook should look like this:

```json
{
  "data": {"first_name": "John", "last_name": "Doe"},
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "c2f98143c6043db3a67d530a467353e92e54e63dd6ca17d44ea0e1a37cf9cce6"
}
```

And given my client secret is `c57f41ac-3bfb-4bb5-b18f-00cca093d97b`. Then I would construct input string as `$first_name|$last_name|$none|$client_secret`:

```
John|Doe|YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5|c57f41ac-3bfb-4bb5-b18f-00cca093d97b
```

This string is then `SHA256`, `BASE16` and down cased. Result should be:

```
c2f98143c6043db3a67d530a467353e92e54e63dd6ca17d44ea0e1a37cf9cce6
```

If signature is valid, it should be same as signature parameter.

Parameters for signature should be in this order:

- platform
- start_time
- finish_time,
- client_ip
- client_ip_country
- client_location
- overall
- suspicious_reasons
- mismatch_tags
- fraud_tags
- auto_document
- auto_face
- manual_document
- manual_face
- aditional_steps
- document_valid_until
- document_type
- document_number
- id
- provided_email
- provided_name
- provided_surname
- provided_is_pep
- provided_is_sanctioned
- bank_account_requested
- bank_account_unsupported_integration
- bank_account_owner_name
- bank_account_iban
- identity_verification_failed

In case of `"identity_verification_failed": true`, identity documents are omitted and only these attribuptes are used:

- id
- provided_email
- provided_name
- provided_surname
- provided_is_pep
- provided_is_sanctioned
- bank_account_requested
- bank_account_unsupported_integration
- bank_account_owner_name
- bank_account_iban
- identity_verification_failed

## Testing

Since on sandbox we cannot process real banking data, there is mockup of bank running. It always return account owner name `John Doe` and responds with IBAN `SK5111110000000002314003` in case of unicredit and `SK0431000000002333363431` in case of other bank integration.

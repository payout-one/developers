# Identity verification and bank account owner retrieval

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

You need to retrieve this token using [client credentials claim](./oauth2.md), there you need to request scope `verify`, if you want to do user document verification, or you can also add `account_info` scope, if you want to retrieve client bank account details.

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
    "id": "1b21d842-7f7c-4cdb-a9c5-fff6b94b431b",
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
    "suspicious_reasons": null
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "e1a4ae0ec1596bb8e97e23a4f08ea9d138ab1b0d2f6288b547cacd79e1e7ee88"
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
    "id": "1b21d842-7f7c-4cdb-a9c5-fff6b94b431b",
    "identity_verification_failed": true,
    "provided_email": "john.doe@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "John",
    "provided_surname": "Doe"
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "f80dfb89fdd29ea5b7b663191683da3fb6e692de269bc7c3f0e75fdc3f19be48"
}
```

Webhook when also account details are returned:

```json

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
    "id": "8086d82b-c33d-46ac-895f-9828812c5060",
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
    "suspicious_reasons": null
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "8c087253ec624256a3a3e764d6ad9030c605bf71061d672cb3d694c26a7283a3"
}
```

Webhook in case user choose that does not have account in any of supported banks:

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
    "id": "6548c7e0-9e2f-4414-bd36-40e505425ff9",
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
    "suspicious_reasons": null
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "c98d3e1d1f02968a57a1a22d9696e9634714a12771d7219be446bcbd08519816"
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

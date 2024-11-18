# Identity verification

   > [!NOTE]
   > This API is still heavily developed and can change in next release

PayoutID also provides identity verification and AML. It uses custom endpoint which will return redirect to start user verifications. After user provides all required data, he is redirected back to client. Since we get results from some checks asynchronously, result is delivered as webhook. This api requires to retrieve access token with `verify` scope. In case you want to ask for account details, `account_info` scope is required. For AML `aml` scope is required.

Process is as follows:

1. retrieve access token
2. retrieve redirect from verification invitation endpoint
3. redirect user to retrieve redirect uri
4. wait for webhook

Whole process can be on following diagram:

![Payout ID verification diagram](../_media/payout-id-verification.png)

Documentation for verification invitation endpoint can be found [here](https://documenter.getpostman.com/view/10478778/2s9YsFDYzn#08658c94-347c-448d-9b16-8c7cfcb0f3d0)

## Retrieving access token

You need to retrieve this token using `client credentials grant`, with required scope `verify` and optional scopes `account_info`, in case you want to retrieve client bank account details, and `aml` in case you want to retrieve list where verified user is present. [Here](https://documenter.getpostman.com/view/10478778/2s9YsFDYzn#f885ffae-52a8-47b8-86e1-decceb9fec2c) you will find documentation for access token endpoint.

## Webhooks

After data is collected, it is sent to the client using webhooks. There are two types of webhooks:
1. Identity verification webhook (sent to `notify_url`)
2. AML check webhook (sent to `aml_notify_url`)

Both webhooks are signed and clients should verify signatures to prevent fraudulent calls. Webhooks are delivered using `POST` method.

### Identity Verification Webhook

This webhook contains the result of identity verification and bank account details (if requested). It is sent to the URL provided as `notify_url` in the invitation request.

#### Attributes

Webhook will contain following attributes:

| path | type | required | example | description |
| ---- | ---- | --- | --- | --- |
| type | string | yes | IDENTITY_CHECK | Webhook Type |
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
| data/document_front_url | string | no | - | URL to download front photo of used document. URL will expire in one hour. |
| data/document_back_url | string | no | - | URL to download back photo of used document. URL will expire in one hour. |
| data/document_first_name | string | no | - | First name scanned from the document |
| data/document_last_name | string | no | - | Last name scanned from the document |
| data/document_sex | string | no | - | | Sex scanned from the document |
| data/document_nationality | string | no | - | Nationality scanned from the document |
| data/document_issuing_country | string | no | - | Issuing country of the document |
| data/document_birth_place | string | no | - | Birth place scanned from the document |
| data/document_person_code | string | no | - | Personal code scanned from the document |
| data/document_date_of_birth | string | no | - | Date of birth scanned from the document |
| data/photo_face_url | string | no | - | URL download face photo of user. URL will expire in one hour. |
| data/platform | string | - | - | - |
| data/manual_face | string | no | "FACE_MATCH" | Result of manual examination of photos |
| data/mismatch_tags | array of strings | no | [] | List of mismatched attributes from document |
| data/manual_document | string | no | "DOC_VALIDATED" | - |
| data/aml_requested | boolean | no | false | If also AML checks are required |
| data/aml_request_failed | boolean | no | false | - |
| data/aml_error_message | string | no | - | - |
| data/aml_status_service_suspected | boolean | no | - | - |
| data/aml_status_service_used | boolean | no | - | - |
| data/aml_status_service_found | boolean | no | - | - |
| data/aml_status_check_successfull | boolean | no | - | - |
| data/aml_status_overall | string | no | "SUSPECTED" | Overall result of check |
| data/aml_error_message | string | no | - | - |
| data/aml_uid | string | no | - | - |
| data/aml_items | array of [AML Item](#aml-item) | no | [] | - |
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



### AML Check Webhook

This webhook contains AML check results. It is sent to the URL provided as `aml_notify_url` in the invitation request. Multiple AML check webhooks might be delivered for a single invitation as the monitoring continues.

#### Attributes

Webhook will contain following attributes:

| path | type | required | example | description |
| ---- | ---- | --- | --- | --- |
| type | string | yes | AML_CHECK | Webhook Type |
| data | object | yes | - | contains all data |
| data/id | string | yes | "edf29e60-45a5-463b-b120-033e835df3ce" | identificator of invitation, should be same as in invitation create response |
| data/aml_request_failed | boolean | no | false | - |
| data/aml_error_message | string | no | - | - |
| data/aml_status_service_suspected | boolean | no | - | - |
| data/aml_status_service_used | boolean | no | - | - |
| data/aml_status_service_found | boolean | no | - | - |
| data/aml_status_check_successfull | boolean | no | - | - |
| data/aml_status_overall | string | no | "SUSPECTED" | Overall result of check |
| data/aml_error_message | string | no | - | - |
| data/aml_uid | string | no | - | - |
| data/aml_items | array of [AML Item](#aml-item) | no | [] | - |
| signature | string | yes | - | Signature to verify origin of the returned data |
| nonce | string | yes | - | Used to sign data |


#### AML Item

| path | type | required | example | description |
| ---- | ---- | --- | --- | --- |
| name | string | yes | - | - |
| surname | string | yes | - | - |
| reason | string | yes | - | - |
| nationality | string | yes | - | - |
| dob | string |yes | - | - |
| suspicion | string | yes | "PEPS" | One of PEPS, SANCTION, INTERPOL or OTHER |
| list_number | string | yes | - | - |
| list_name | string | yes | - | - |
| score | integer | yes | - | - |
| last_update | date | yes | - | - |
| is_person | boolean | yes | - | - |
| is_active | boolean | yes | - | - |
| linked_document | string | yes | - | - |
| other_information | string | yes | - | - |
| checked_at | string | yes | - | - |

### Examples

Successful Identity Verification Webhook:

``` json
{
  "data": {
    "provided_email": "test@test.ti",
    "id": "13b0f350-e208-4440-8f7c-cdae9d597f6d",
    "document_type": "PASSPORT",
    "identity_verification_failed": false,
    "client_ip": "177.77.77.196",
    "bank_account_requested": false,
    "finish_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": [],
    "document_valid_until": "2024-03-09",
    "auto_document": "DOC_VALIDATED",
    "overall": "APPROVED",
    "fraud_tags": [],
    "provided_is_sanctioned": false,
    "document_birth_place": "LONDON",
    "document_first_name": "JOHN",
    "document_nationality": "NL",
    "document_personal_code": "801012/8420",
    "document_date_of_birth": "1980-10-12",
    "start_time": "2023-12-07T13:16:44Z",
    "document_last_name": "DOE",
    "auto_face": "FACE_MATCH",
    "document_issuing_country": "NL",
    "aditional_steps": null,
    "provided_surname": "Doe",
    "bank_account_unsupported_integration": false,
    "document_number": "DE4878783",
    "platform": "PC",
    "document_back_url": "http://localhost:9000/payout-id/identity_verifications/0dc0ceea-1a7d-4f66-abb6-7eb653b1411e/document_back.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T113901Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=ce9c49cd6a11ef0e41d1f79ab794a1b6fc04506ee053bbff6039796ae9952833",
    "manual_face": "FACE_MATCH",
    "client_ip_country": "LT",
    "client_location": "Kaunas, Lithuania",
    "bank_account_iban": null,
    "document_sex": "MALE",
    "provided_name": "John",
    "mismatch_tags": [],
    "document_front_url": "http://localhost:9000/payout-id/identity_verifications/0dc0ceea-1a7d-4f66-abb6-7eb653b1411e/document_front.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T113901Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=3e11e28fd977974d6115e2722fd25a81a67336e4b2dfecd21ceb8e477a3cfcb7",
    "photo_face_url": "http://localhost:9000/payout-id/identity_verifications/0dc0ceea-1a7d-4f66-abb6-7eb653b1411e/photo_face.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T113901Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=abae5f1cb3b2e19a7145b98339ec0b66c132fd2e59dc19271a48cb1f15acaf48",
    "provided_is_pep": false,
    "bank_account_owner_name": null,
    "manual_document": "DOC_VALIDATED"
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "73c9842f5512e1cba56c22b6522efa76d55cadb87f5b9d440e5b459ab4ff4e96"
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
    "provided_email": "email@example.com",
    "id": "d4130224-cab4-4b22-b8bc-d38f0a333b4a",
    "document_type": "PASSPORT",
    "identity_verification_failed": false,
    "client_ip": "177.77.77.196",
    "bank_account_requested": true,
    "finish_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": [],
    "document_valid_until": "2024-03-09",
    "auto_document": "DOC_VALIDATED",
    "overall": "APPROVED",
    "fraud_tags": [],
    "provided_is_sanctioned": false,
    "document_birth_place": "LONDON",
    "document_first_name": "JOHN",
    "document_nationality": "NL",
    "document_personal_code": "801012/8420",
    "document_date_of_birth": "1980-10-12",
    "start_time": "2023-12-07T13:16:44Z",
    "document_last_name": "DOE",
    "auto_face": "FACE_MATCH",
    "document_issuing_country": "NL",
    "aditional_steps": null,
    "provided_surname": "Priezvisko4",
    "bank_account_unsupported_integration": false,
    "document_number": "DE4878783",
    "platform": "PC",
    "document_back_url": "http://localhost:9000/payout-id/identity_verifications/ec00b1c5-d3f3-4977-8d1d-15e55f62c91c/document_back.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T115451Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=f92536362175c599694ce37dcc405b409d44d31a6f8bcd8a240a598157692f0a",
    "manual_face": "FACE_MATCH",
    "client_ip_country": "LT",
    "client_location": "Kaunas, Lithuania",
    "bank_account_iban": "SK5111110000000002314003",
    "document_sex": "MALE",
    "provided_name": "Meno4",
    "mismatch_tags": [],
    "document_front_url": "http://localhost:9000/payout-id/identity_verifications/ec00b1c5-d3f3-4977-8d1d-15e55f62c91c/document_front.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T115451Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=2a4895e6b29d8d80a2fc26a3688564f8fb6db9a9b3d498a4a24788102203a5ef",
    "photo_face_url": "http://localhost:9000/payout-id/identity_verifications/ec00b1c5-d3f3-4977-8d1d-15e55f62c91c/photo_face.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T115451Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=4ff557d7dd529b32cf544cea71f2d15d6d2aac7d2d9968c6d78d8a6cab7064cd",
    "provided_is_pep": false,
    "bank_account_owner_name": "Rostislav Stefanik",
    "manual_document": "DOC_VALIDATED"
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "8e4c1f2a9b3d567890e12345f6789abcd0123456789abcdef0123456789abcdef"
}
```

Webhook in case user chooses that he does not have account in any of supported banks:

``` json
{
  "data": {
    "provided_email": "email@example.com",
    "id": "f28da883-b68d-46ce-ab00-0a8a88f15f72",
    "document_type": "PASSPORT",
    "identity_verification_failed": false,
    "client_ip": "177.77.77.196",
    "bank_account_requested": true,
    "finish_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": [],
    "document_valid_until": "2024-03-09",
    "auto_document": "DOC_VALIDATED",
    "overall": "APPROVED",
    "fraud_tags": [],
    "provided_is_sanctioned": false,
    "document_birth_place": "LONDON",
    "document_first_name": "JOHN",
    "document_nationality": "NL",
    "document_personal_code": "801012/8420",
    "document_date_of_birth": "1980-10-12",
    "start_time": "2023-12-07T13:16:44Z",
    "document_last_name": "DOE",
    "auto_face": "FACE_MATCH",
    "document_issuing_country": "NL",
    "aditional_steps": null,
    "provided_surname": "Doe",
    "bank_account_unsupported_integration": true,
    "document_number": "DE4878783",
    "platform": "PC",
    "document_back_url": "http://localhost:9000/payout-id/identity_verifications/a1cde168-df76-431d-81e7-d67a51d2db37/document_back.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T120035Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=289224190ca2a1cd2d333411990f13262970c602b83c2d1ad2d9c5ae631fb1dd",
    "manual_face": "FACE_MATCH",
    "client_ip_country": "LT",
    "client_location": "Kaunas, Lithuania",
    "bank_account_iban": null,
    "document_sex": "MALE",
    "provided_name": "John",
    "mismatch_tags": [],
    "document_front_url": "http://localhost:9000/payout-id/identity_verifications/a1cde168-df76-431d-81e7-d67a51d2db37/document_front.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T120035Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=ef0fb0445f8ad4ab7d0d4a322f312b54281b80ff102a0ee2383de3ad24a64430",
    "photo_face_url": "http://localhost:9000/payout-id/identity_verifications/a1cde168-df76-431d-81e7-d67a51d2db37/photo_face.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20241101%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20241101T120035Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=c525775c637e42e5a37afff0f0c586feacfd56d2a07f421125fbb8d58b49cd0c",
    "provided_is_pep": false,
    "bank_account_owner_name": null,
    "manual_document": "DOC_VALIDATED"
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "b9a87c65d4e3f210987654321fedcba0123456789abcdef0123456789abcdef01"
}
```

AML Check Webhook:

```json
{
  "data": {
    "id": "b93e7497-1726-4216-8516-df678d86ca03",
    "status_service_suspected": true,
    "status_service_used": true,
    "status_service_found": true,
    "status_check_successful": true,
    "status_overall": "SUSPECTED",
    "error_message": null,
    "uid": "FAFQLS95W7Z0JI9HL13VZBMX6",
    "items": [
      {
        "checked_at": "2023-10-11T15:28:21Z",
        "dob": "31 AUG 1954",
        "is_active": true,
        "is_person": true,
        "last_update": "2022-03-16",
        "linked_document": "https://sanctionssearch.ofac.treas.gov/Details.aspx?id=9760",
        "list_name": "OFAC",
        "list_number": "UNKNOWN",
        "name": "JOHN SIMPSON",
        "nationality": "BELARUS",
        "other_information": null,
        "reason": "BELARUS PROGRAM",
        "score": 100,
        "surname": "DOE",
        "suspicion": "SANCTION"
      },
      {
        "checked_at": "2023-10-11T15:28:21Z",
        "dob": "30 AUG 1954",
        "is_active": true,
        "is_person": true,
        "last_update": "2022-03-16",
        "linked_document": "https://sanctionssearch.ofac.treas.gov/Details.aspx?id=9760",
        "list_name": "OFAC",
        "list_number": "UNKNOWN",
        "name": "JOHN SIMPSON",
        "nationality": "BELARUS",
        "other_information": null,
        "reason": "BELARUS PROGRAM",
        "score": 100,
        "surname": "DOE",
        "suspicion": "SANCTION"
      },
      {
        "checked_at": "2023-10-11T15:28:21Z",
        "dob": "1954",
        "is_active": true,
        "is_person": true,
        "last_update": "2022-07-08",
        "linked_document": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv%3AOJ.L_.2021.068.01.0029.01.ENG&toc=OJ%3AL%3A2021%3A068%3ATOC",
        "list_name": "EU",
        "list_number": "UNKNOWN",
        "name": "JOHN SIMPSON",
        "nationality": "BELARUS",
        "other_information": "UNKNOWN",
        "reason": "EU.5971.83 ",
        "score": 100,
        "surname": "DOE",
        "suspicion": "SANCTION"
      }
    ]
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "2e2e8ebdad9aacda677d28288edf6cb2e531f77dc15b357ecdc4663bbcf78c2e"
}
```

### Signature

To verify signature, you need to concat all returned values from data, nonce and you client secret. These data should be separated using pipe `|`. In case of arrays in the response, they are concatenated without any separator, so `["test", "value"]` became `"testvalue"`. Boolean values are represented in resulting string as `true` and `false` strings. Empty array (`[]`) or `null` are represented as empty strings. Resulting string is then neceseary to hash using `SHA256` algorithm. Then it should be base16 encoded and all character should be downcased. For instance if I have imaginary webhook containing parameters first_name, last_name, children, married, age and hobies then webhook should look like this:

```json
{
  "data": {"first_name": "John", "last_name": "Doe", "children": [], "married": true, "age": null, "hobies": ["guitar", "skying"]},
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "25c304386d0195803370da336d46919933fc64397b8e59c669aed90b5ec58ba8"
}
```

And given my client secret is `c57f41ac-3bfb-4bb5-b18f-00cca093d97b`. Then I would construct input string as `$first_name|$last_name|$children|$married|$age|$hobies|$nonce|$client_secret`:

```
John|Doe||true||guitarskying|YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5|c57f41ac-3bfb-4bb5-b18f-00cca093d97b
```

This string is then `SHA256`, `BASE16` and down cased. Result should be:

```
25c304386d0195803370da336d46919933fc64397b8e59c669aed90b5ec58ba8
```

If signature is valid, it should be same as signature parameter.

For Identity Verification webhook, parameters should be in this order::

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
- document_first_name
- document_last_name
- document_sex
- document_nationality
- document_issuing_country
- document_birth_place
- document_personal_code
- document_date_of_birth
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

For AML Check webhook, parameters for signature should be in this order:

- id
- status_service_suspected
- status_service_used
- status_service_found
- status_check_successful
- status_overall
- error_message
- uid

## Testing

Since on sandbox we cannot process real banking data, there is mockup of bank running. It always return account owner name `John Doe` and responds with IBAN `SK5111110000000002314003` in case of unicredit and `SK0431000000002333363431` in case of other bank integration.

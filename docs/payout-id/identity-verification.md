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
| data/document_front_url | string | no | - | URL to download front photo of used document. URL will expire in one hour. |
| data/document_back_url | string | no | - | URL to download back photo of used document. URL will expire in one hour. |
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
    "document_back_url": "http://example.com/payout-id/identity_verifications/149cd9bc-85c8-4c54-9532-40d44c72d5dc/document_back.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T163735Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=fbb9c5200fc73009a2b9145109a0df69b0ba8008792236e3389bff990e01d304",
    "document_front_url": "http://example.com/payout-id/identity_verifications/149cd9bc-85c8-4c54-9532-40d44c72d5dc/document_front.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T163735Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=3bbf4bb428f92306836dad903a505508d26f286ca08da235a9ef54c3558a1658",
    "document_number": "DE4878783",
    "document_type": "PASSPORT",
    "document_valid_until": "2024-03-09",
    "finish_time": "2023-12-07T13:16:44Z",
    "fraud_tags": [],
    "id": "2b7fc719-8450-420f-a10b-131bfbe033ec",
    "identity_verification_failed": false,
    "manual_document": "DOC_VALIDATED",
    "manual_face": "FACE_MATCH",
    "mismatch_tags": [],
    "overall": "APPROVED",
    "photo_face_url": "http://example.com/payout-id/identity_verifications/149cd9bc-85c8-4c54-9532-40d44c72d5dc/photo_face.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T163735Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=ef217de069b25e4c75db1cd0038285f142e2bc6ffb9b45c9aefa92dd6d401e53",
    "platform": "PC",
    "provided_email": "email@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "Meno4",
    "provided_surname": "Priezvisko4",
    "start_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": []
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "b9b4b4d73d42638642915bc5aa007dfc423611bccc53d8d6fe3c84fd5b2e4b9d"
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
    "bank_account_owner_name": "Meno 877031 Priezvisko 877031",
    "bank_account_requested": true,
    "bank_account_unsupported_integration": false,
    "client_ip": "177.77.77.196",
    "client_ip_country": "LT",
    "client_location": "Kaunas, Lithuania",
    "document_back_url": "http://example.com/payout-id/identity_verifications/406c4a41-45b6-4e4c-a9fe-76a536c39877/document_back.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164018Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=d036ea801dddcb9b58abb1b79f0af575d39de1edfbc09a48e6e30c8ab97e31ff",
    "document_front_url": "http://example.com/payout-id/identity_verifications/406c4a41-45b6-4e4c-a9fe-76a536c39877/document_front.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164018Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=c15323baadc7139af9d67f593a6fdc8f32060e79dff368b1289506a2a5fbbb53",
    "document_number": "DE4878783",
    "document_type": "PASSPORT",
    "document_valid_until": "2024-03-09",
    "finish_time": "2023-12-07T13:16:44Z",
    "fraud_tags": [],
    "id": "42aaaec7-2d63-453a-b8a2-0a32eed4b84d",
    "identity_verification_failed": false,
    "manual_document": "DOC_VALIDATED",
    "manual_face": "FACE_MATCH",
    "mismatch_tags": [],
    "overall": "APPROVED",
    "photo_face_url": "http://example.com/payout-id/identity_verifications/406c4a41-45b6-4e4c-a9fe-76a536c39877/photo_face.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164018Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=e86f3b9eef0fbd681f0450761638459bcb7e2ed4d96e9a7e8f8f7339c9900e58",
    "platform": "PC",
    "provided_email": "email@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "Meno4",
    "provided_surname": "Priezvisko4",
    "start_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": []
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "18470be7f4a959ff701ae4b6ee29640c5474287624a74c7bd6f4da396d702237"
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
    "document_back_url": "http://example.com/payout-id/identity_verifications/7cf500a5-9863-43aa-90c0-a9d24c58f931/document_back.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164150Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=62ca9fa92fb5cae70b78db2df711b8e738b454b56f3e010308ae40af05e96821",
    "document_front_url": "http://example.com/payout-id/identity_verifications/7cf500a5-9863-43aa-90c0-a9d24c58f931/document_front.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164150Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=d178bf3cc21015b21596bc71ef11556fea4490730edb35a13574c963cb1b9269",
    "document_number": "DE4878783",
    "document_type": "PASSPORT",
    "document_valid_until": "2024-03-09",
    "finish_time": "2023-12-07T13:16:44Z",
    "fraud_tags": [],
    "id": "5a1f9cd6-21a7-4547-8976-489a8c82e62b",
    "identity_verification_failed": false,
    "manual_document": "DOC_VALIDATED",
    "manual_face": "FACE_MATCH",
    "mismatch_tags": [],
    "overall": "APPROVED",
    "photo_face_url": "http://example.com/payout-id/identity_verifications/7cf500a5-9863-43aa-90c0-a9d24c58f931/photo_face.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164150Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=f1c82b28f0c2520ba192686e0421ebd8fb03f05e60a9fc3983fb8bd0836b3721",
    "platform": "PC",
    "provided_email": "email@example.com",
    "provided_is_pep": false,
    "provided_is_sanctioned": false,
    "provided_name": "Meno4",
    "provided_surname": "Priezvisko4",
    "start_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": []
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "6191e5ebc70435f499d7190838773012222d2988d2f1d56c97498df05018c1a9"
}
```

Webhook with aml data:

```json
{
  "data": {
    "provided_email": "email@example.com",
    "id": "0b817c2f-9248-4643-a3c6-a59946b47aef",
    "document_type": "PASSPORT",
    "identity_verification_failed": false,
    "client_ip": "177.77.77.196",
    "bank_account_requested": false,
    "finish_time": "2023-12-07T13:16:44Z",
    "suspicion_reasons": [],
    "document_valid_until": "2024-03-09",
    "auto_document": "DOC_VALIDATED",
    "aml_status_overall": "SUSPECTED",
    "overall": "APPROVED",
    "fraud_tags": [],
    "aml_status_service_suspected": true,
    "aml_error_message": null,
    "provided_is_sanctioned": false,
    "aml_status_service_found": true,
    "aml_requested": true,
    "start_time": "2023-12-07T13:16:44Z",
    "auto_face": "FACE_MATCH",
    "aditional_steps": null,
    "provided_surname": "Priezvisko4",
    "bank_account_unsupported_integration": false,
    "document_number": "DE4878783",
    "platform": "PC",
    "document_back_url": "http://example.com/payout-id/identity_verifications/ccd8ecff-38fe-47b7-928d-6b50099502b8/document_back.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164342Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=b35ebef910e4c5cf09ef4a4cf59b2516774b2cc027c6d43a5074375a2d2cdc8b",
    "aml_request_failed": null,
    "manual_face": "FACE_MATCH",
    "client_ip_country": "LT",
    "aml_uid": "FAFQLS95W7Z0JI9HL13VZBMX6",
    "client_location": "Kaunas, Lithuania",
    "bank_account_iban": null,
    "provided_name": "Meno4",
    "mismatch_tags": [],
    "aml_items": [
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
    ],
    "document_front_url": "http://example.com/payout-id/identity_verifications/ccd8ecff-38fe-47b7-928d-6b50099502b8/document_front.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164342Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=203fef77773dafa3e0f4e732bc86bbfd07a807e483f86963f7c49eac3235dac9",
    "aml_status_service_used": true,
    "photo_face_url": "http://example.com/payout-id/identity_verifications/ccd8ecff-38fe-47b7-928d-6b50099502b8/photo_face.png?response-content-disposition=attachment&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=kc8AJeOICZodU2ZahIXP%2F20240701%2Flocal%2Fs3%2Faws4_request&X-Amz-Date=20240701T164342Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=4d70d11f6f0bab48846cd1335c56313a14fc4a61f47596f1a9dacb3d80a6ebb0",
    "provided_is_pep": false,
    "bank_account_owner_name": null,
    "aml_status_check_successfull": true,
    "manual_document": "DOC_VALIDATED"
  },
  "nonce": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5",
  "signature": "75eedf0896558de2991de0a491988cf27f149b890ecf10bb999e39c0cddd2432"
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

In case of AML, those attributes are also included in signature, they are added at the end of signed string:

- aml_requested,
- aml_request_failed,
- aml_status_service_suspected,
- aml_status_service_used,
- aml_status_service_found,
- aml_status_check_successfull,
- aml_status_overall,
- aml_error_message,
- aml_uid

## Testing

Since on sandbox we cannot process real banking data, there is mockup of bank running. It always return account owner name `John Doe` and responds with IBAN `SK5111110000000002314003` in case of unicredit and `SK0431000000002333363431` in case of other bank integration.

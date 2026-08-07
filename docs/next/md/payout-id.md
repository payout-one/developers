# PayoutID OAuth2

## Authorization redirect for user

`GET /oauth/authorize`

Endpoint where client should redirect user for authorization

### Example

```bash
curl -X GET https://app.payout.one/oauth/authorize \
  -H "Authorization: Bearer $TOKEN"
```


## Endpoint to retrieve authorization token

`POST /oauth/token`

Endpoint where client can retrieve authorization token after successfull
authorization or refresh expired access token with valid refresh token

### Example

```bash
curl -X POST https://app.payout.one/oauth/token \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
       "grant_type": "authorization_code",
       "client_id": "2591CF97-1AFB-4D63-8B42-2D0CD6194CAF",
       "client_secret": "4c4f4df3-d026--8c4b-98e0434c882a",
       "code": "8167B030-A72A-466E-9EDC-7377B15C9C7B",
       "redirect_uri": "https://example.com",
       "code_verifier": "60ac297b-c100-42ce-be0d-46b14a0b0hee"
     }'
```


## Sign Out

`GET /id/sessions/external`

Redirect to ask currently logged in user in PayoutID to log out, after successful logout, user is redirected back to application.

[  
](https://desktop.postman.com/?desktopVersion=10.5.2&userId=10478778&teamId=59082)

### Example

```bash
curl -X GET https://app.payout.one/id/sessions/external \
  -H "Authorization: Bearer $TOKEN"
```


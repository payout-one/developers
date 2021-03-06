# Payout OAuth2

For authorization of [PSD2](./psd2.md) and [Banklink](./banklink.md) API [OAuth2](https://oauth.net/2/) protocol is used. For now only [authorization code grant](https://www.oauth.com/oauth2-servers/server-side-apps/authorization-code/) and [refresh token grant](https://www.oauth.com/oauth2-servers/making-authenticated-requests/refreshing-an-access-token/) is supported.

## Authorization code grant

In this code grant, when integrator need to receive some data or do any action on behalf of user. He needs first to redirect him to authorization url. There are separate url's for each environment:

- https://sandbox.payout.one/oauth - for sandbox environment
- https://app.payout.one/oauth - for production environment

Authorization flow is going as follow:

1. User need to be redirected to authorization endpoint:
  * for sandbox [https://documenter.getpostman.com/view/10478778/UVz1PD5E#9d71454b-9dd8-4176-aff4-106078460127](https://documenter.getpostman.com/view/10478778/UVz1PD5E#9d71454b-9dd8-4176-aff4-106078460127)
  * for production [https://documenter.getpostman.com/view/10478778/UVz1MXSQ#81a0d91a-c932-46b9-9522-797335a04feb](https://documenter.getpostman.com/view/10478778/UVz1MXSQ#81a0d91a-c932-46b9-9522-797335a04feb)
2. User needs to authenticate self (login or register) and then is asked to approve access to requested scopes to integrator. Possible scopes are descriped in concrete endpoints required them.
3. User is redirected back to integrator with `authorization_code` in query parameters.
4. Integrator uses `authorization_code` to retrieve `access_token` using token endpoint:
  * for sandbox [https://documenter.getpostman.com/view/10478778/UVz1PD5E#d917c8b6-6070-4ffd-b816-4347cf471bbd](https://documenter.getpostman.com/view/10478778/UVz1PD5E#d917c8b6-6070-4ffd-b816-4347cf471bbd)
  * for production [https://documenter.getpostman.com/view/10478778/UVz1MXSQ#0ed344e6-2b8d-447a-8185-c7d784904365](https://documenter.getpostman.com/view/10478778/UVz1MXSQ#0ed344e6-2b8d-447a-8185-c7d784904365)
5. Integrator now can work with chosen endpoint passing `access_token` in `Authorization` header.

This flow also can be seen at next diagram:

![Authorization code flow sequence diagram](./_media/authorization_code_flow.png)



## Refresh token grant
  
Authorization code is time constrained. For security reason, expiration times are short and should not be longer that one hour. To allow for longer access to resource, refresh token is issued with every authorization code access token which can have expiration time up to 90 days. Hovever, it is not alloweed to access endpoints with this token and only can be used to issue new `access_token`.

This token is issued by passing `refresh_token` as `grant` and retrieved refresh token as `refresh_token` to `token` API:
  * for sandbox [https://documenter.getpostman.com/view/10478778/UVz1PD5E#d917c8b6-6070-4ffd-b816-4347cf471bbd](https://documenter.getpostman.com/view/10478778/UVz1PD5E#d917c8b6-6070-4ffd-b816-4347cf471bbd)
  * for production [https://documenter.getpostman.com/view/10478778/UVz1MXSQ#0ed344e6-2b8d-447a-8185-c7d784904365](https://documenter.getpostman.com/view/10478778/UVz1MXSQ#0ed344e6-2b8d-447a-8185-c7d784904365)

## Banklink accounts

From user point of view, process is different for issuing access token for [Banklink](./banklink.md). In this case it is also required to have banklink account. In case he does not have it, he is requested to create one as intermediate step betwen login/registration and granting access to his account to integrator. Sequence diagram which includes account creation can be seen next:

![Banklink authorization code flow sequence diagram](./_media/banklink_authorization_code_flow.png)

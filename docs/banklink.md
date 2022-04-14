# Banklink API

Banklink API is service that allow to access user's bank information through unified API. This API is based on PSD2 API and is copying it to some extend, hovever it is limited by different standards and implementations by banks. This API can onli by accessed on behalf of user by receiving access token using [Payout OAuth2](./oauth2.md). To access these API-s, integrator need's to retrieve `BLAISP` scope for reading details, balances or transactions of user account or `BLIBAN` to be able to verify if authorized user has access to acount with such IBAN.

Documentation for concrete endpoints:
- [production](https://wap.payout.one/api-docs)
- [sandbox](https://wap-sa.payout.one/api-docs)

On next sequence diagram, we can see flow of calls, OAuth2 authorization code flow is omited since it is described in it's own [section](./oauth2.md), this diagram is for account details requests, but same flow will work for all other calls, besides call to list connected accounts, which does not request data from bank, onli shoving data from Banklink database, so there is no SCA between client and Bank:

![Retrieve account details using Banklink API](./_media/banklink_account_details.png)

Required scopes for OAuth2 are described in endpoint documentation.

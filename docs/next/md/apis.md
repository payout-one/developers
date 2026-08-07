# API References

Self-hosted references are generated from the API collections and served from this
site. The Postman links remain live until the migration is finished — see
[status](#migration-status) below.

| API | Reference | Current (Postman) |
| --- | --- | --- |
| Payment API (main) | [Reference](/api/payment/index.html ':ignore Payment API reference') | [postman.payout.one](https://postman.payout.one/) |
| Intel API | [Reference](/api/intel/index.html ':ignore Intel API reference') | [postman-intel.payout.one](https://postman-intel.payout.one/) |
| OpenBanking PSD2 API | [Reference](/api/psd2/index.html ':ignore PSD2 API reference') | [psd2.payout.one](https://psd2.payout.one/) |
| Banklink API | [Reference](/api/banklink/index.html ':ignore Banklink API reference') | [Sandbox](https://documenter.getpostman.com/view/10478778/Uyr4KLLY) · [Production](https://documenter.getpostman.com/view/10478778/Uyr4KfHU) |
| PayoutID OAuth2 | [Reference](/api/payout-id/index.html ':ignore PayoutID OAuth2 reference') | [Sandbox](https://documenter.getpostman.com/view/10478778/UVz1PD5E) · [Production](https://documenter.getpostman.com/view/10478778/UVz1MXSQ) |
| PayoutID Verifications | _not yet migrated_ | [Sandbox](https://documenter.getpostman.com/view/10478778/2s9YsFDYzn#08658c94-347c-448d-9b16-8c7cfcb0f3d0) · [Production](https://documenter.getpostman.com/view/10478778/2sA3QtercC) |

Sandbox and production share one reference each — the environment is the base URL,
not a separate document:

| Environment | Base URL |
| --- | --- |
| Production | `https://app.payout.one` |
| Sandbox | `https://sandbox.payout.one` |

## Migration status

The self-hosted references are a **verbatim port** of the Postman documentation —
same descriptions, tables and samples — so the two can be diffed before Postman is
switched off. Corrections and additions come after the port, not during it.

Known gaps:

- **PayoutID Verifications** has no self-hosted page yet. Its endpoints are split
  across the OAuth2 and PayoutID collections and need merging into one reference.
- **Coverage.** The Payment API reference documents 11 endpoints; the router in
  `payout_api` serves considerably more. Generating the reference from an OpenAPI
  spec produced by the application will close that gap.

## Regenerating

See [`tools/README.md`](https://github.com/payout-one/developers/blob/master/tools/README.md).

```bash
make docs
```

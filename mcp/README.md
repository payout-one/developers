# Payout MCP server

Exposes the Payout API to LLM agents — endpoint lookup plus live calls. Everything
is derived from the OpenAPI specs in `../docs/openapi`, so the agent surface cannot
drift from the published documentation: regenerate the specs and the tools follow.

```bash
cd mcp && npm install
node server.js          # speaks MCP over stdio
```

## Tools

| Tool | Purpose |
| --- | --- |
| `list_endpoints` | Discover what exists. Filter by `api` slug or free-text `search`. |
| `get_endpoint` | Full detail for one operation — parameters, request/response schemas with `$ref`s inlined, and the prose docs. |
| `call_api` | Actually invoke an endpoint. Sandbox by default. |

Each spec is also exposed as a resource (`payout://spec/payment`) for agents that
would rather read the whole document.

The intended sequence is `list_endpoints` → `get_endpoint` → `call_api`; the tool
descriptions steer agents along it so requests are shaped correctly before any
call is made.

## Configuration

| Variable | Effect |
| --- | --- |
| `PAYOUT_CLIENT_ID` / `PAYOUT_CLIENT_SECRET` | Required for `call_api`. Lookup tools work without them. |
| `PAYOUT_ENV` | `sandbox` (default) or `production`. |
| `PAYOUT_ALLOW_PRODUCTION` | Must be exactly `true` before any production call is permitted. |
| `PAYOUT_SPEC_DIR` | Override the spec directory. Defaults to `../docs/openapi`. |

### Claude Code / Claude Desktop

```json
{
  "mcpServers": {
    "payout": {
      "command": "node",
      "args": ["/path/to/developers/mcp/server.js"],
      "env": {
        "PAYOUT_CLIENT_ID": "...",
        "PAYOUT_CLIENT_SECRET": "..."
      }
    }
  }
}
```

Omitting the credentials gives a safe read-only server: agents can still learn the
whole API surface, they just cannot call it.

## Safety

This fronts a payments API, so the defaults are deliberately restrictive.

- **Sandbox only** unless started with `PAYOUT_ALLOW_PRODUCTION=true`. An agent
  asking for `environment: "production"` is refused with an explanation rather
  than silently downgraded — silent downgrades produce confusing results and
  teach agents the wrong model of the system.
- **Spec-bound.** `call_api` refuses any operation not in the spec, so an agent
  cannot invent a path.
- **No credential leakage.** Credentials are read from the environment, never
  returned in a tool result. Authorization failures report the status code only,
  because the response body can echo what was sent.
- **No half-formed requests.** Unsubstituted `{path_params}` are caught before
  the call rather than sent literally.

Tokens are cached in memory for 30 minutes and never written to disk.

## Verified

Exercised over the real MCP protocol with an SDK client:

- 3 tools and 5 spec resources registered; 37 operations indexed across 5 APIs
- `get_endpoint` inlines `$ref`s — `customer` arrives as a full object, not a pointer
- production refused; missing credentials, unknown operation, and missing path
  parameter each produce a clear `isError` result rather than a crash

## Not done yet

- **Coverage** follows the specs, which come from the Postman collections — 10 of
  the ~81 routes `payout_api` serves. Generating the spec from the router closes
  this for the docs and the agent surface at the same time.
- **No write-safety classification.** `create_checkout` and `list_checkouts` are
  treated alike. Sandbox-only makes that acceptable for now, but before
  production is unlocked, mutating operations should require confirmation.
- **stdio transport only.** Fine for local agents; a hosted server for merchant
  agents would need HTTP transport plus per-merchant auth.

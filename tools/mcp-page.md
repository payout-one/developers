<span class="badge badge-beta">Beta</span>

Let your AI agents work against the Payout API. The server exposes tools an agent
can use to search the API surface, read parameter detail, and fetch live data —
over the Model Context Protocol, so it works with any MCP client rather than one
vendor's assistant.

Everything is derived from the same OpenAPI specification that renders this
documentation, so what an agent is told and what is published here cannot drift
apart.

## Endpoint

| Environment | URL |
| --- | --- |
| Sandbox | `https://sandbox.payout.one/mcp` |
| Production | `https://api.payout.one/mcp` |

Start on sandbox. The token you present decides which data the agent sees, so
point it at sandbox credentials while you are evaluating.

Authentication is a bearer token — the one issued by
[`POST /api/v1/authorize`](api/payment.html#authorize_receive_api_token).
No separate credential is needed, and an agent can never reach anything that
token could not.

> **Beta.** Read-only for now: agents can search the API, read parameter detail
> and perform `GET` requests. Write tools are not yet exposed — see
> [Scope](#scope).

## Get a token

The MCP server authenticates with the same bearer token as the REST API. Exchange
your API credentials — `client_id` and `client_secret` from the Admin section of
your account — for one:

```bash
export CLIENT_ID='your-client-id'
export CLIENT_SECRET='your-client-secret'

export PAYOUT_TOKEN=$(curl -s -X POST https://sandbox.payout.one/api/v1/authorize \
  -H "Content-Type: application/json" \
  -d "{\"client_id\":\"$CLIENT_ID\",\"client_secret\":\"$CLIENT_SECRET\"}" \
  | jq -r '.token')

echo "token length: ${#PAYOUT_TOKEN}"
```

A non-zero length means you have a token. `PAYOUT_TOKEN` is what the commands
below expect.

> **The token expires after 100 minutes.** The MCP client stores whatever you
> gave it, so once the token lapses every call returns `401` and the server looks
> broken when it is not. Removing this step is the next thing on the roadmap —
> see [Scope](#scope).

Until then, mint a fresh token and re-add the server:

```bash
claude mcp remove payout
claude mcp add --transport http payout https://sandbox.payout.one/mcp \
  --header "Authorization: Bearer $PAYOUT_TOKEN"
```

## Connect

<div class="tabs" data-tabs markdown="1">
  <div class="tab-bar" role="tablist">
    <button role="tab" data-tab="claude" aria-selected="true">Claude Code</button>
    <button role="tab" data-tab="cursor" aria-selected="false">Cursor</button>
    <button role="tab" data-tab="vscode" aria-selected="false">VS Code</button>
    <button role="tab" data-tab="codex" aria-selected="false">Codex</button>
    <button role="tab" data-tab="other" aria-selected="false">Other</button>
  </div>

  <div class="tab-pane" data-tab="claude" markdown="1">

Add the server in one command:

```bash
claude mcp add --transport http payout https://sandbox.payout.one/mcp \
  --header "Authorization: Bearer $PAYOUT_TOKEN"
```

Swap the host for `api.payout.one` once you move to production.

Then confirm it is connected:

```bash
claude mcp list
```

Inside a session, `/mcp` shows the server and the tools it offers.

  </div>

  <div class="tab-pane" data-tab="cursor" hidden markdown="1">

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "payout": {
      "type": "http",
      "url": "https://sandbox.payout.one/mcp",
      "headers": {
        "Authorization": "Bearer ${input:payout-token}"
      }
    }
  }
}
```

Cursor prompts for the token the first time the server is used.

  </div>

  <div class="tab-pane" data-tab="vscode" hidden markdown="1">

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "payout": {
      "type": "http",
      "url": "https://sandbox.payout.one/mcp",
      "headers": {
        "Authorization": "Bearer ${input:payout-token}"
      }
    }
  }
}
```

Committing this file shares the server with your team; the token stays local
because it is supplied as an input rather than a literal.

  </div>

  <div class="tab-pane" data-tab="codex" hidden markdown="1">

Codex connects over stdio, so bridge the HTTP endpoint. Add to
`~/.codex/config.toml`:

```toml
[mcp_servers.payout]
command = "npx"
args = [
  "-y", "mcp-remote",
  "https://sandbox.payout.one/mcp",
  "--header", "Authorization: Bearer ${PAYOUT_TOKEN}"
]
```

Export `PAYOUT_TOKEN` in the environment Codex runs in.

  </div>

  <div class="tab-pane" data-tab="other" hidden markdown="1">

Any MCP client that speaks Streamable HTTP can connect directly to
`https://sandbox.payout.one/mcp` with an `Authorization: Bearer` header.

For clients that only support stdio, bridge it:

```bash
npx mcp-remote https://sandbox.payout.one/mcp \
  --header "Authorization: Bearer $PAYOUT_TOKEN"
```

  </div>
</div>

## Tools

| Resource | Tool | Description |
| --- | --- | --- |
| API | `payout_api_search` | Search Payout API endpoints by keyword. |
| API | `payout_api_details` | Detailed parameter information for one endpoint, with schema references resolved. |
| API | `payout_api_read` | Read data with any Payout API `GET` method. |

Each specification is also exposed as a resource (`payout://spec/payment`) for
agents that would rather read the whole document.

The intended sequence is **search → details → read**. Reading the detail before
calling matters: it returns the required fields and their constraints, which is
what stops an agent guessing at a request.

### Example

```
1. payout_api_search   { "search": "withdrawal" }
2. payout_api_details  { "operationId": "retrieve_withdrawal" }
3. payout_api_read     { "operationId": "retrieve_withdrawal",
                         "pathParams": { "withdrawal_id": "…" } }
```

## Safety

This fronts a payments API, so the defaults are restrictive.

> **Enable human confirmation for tool calls**, and be careful when running the
> Payout MCP server alongside other MCP servers. A malicious or compromised
> server can attempt prompt injection — instructing your agent to call tools it
> should not. Treat tool output from any server as untrusted input.

- **No write access.** Nothing exposed here can move money or mutate state.
  `payout_api_read` refuses anything that is not a `GET`.
- **Same authorisation as the REST API.** Requests pass through the API's
  existing authorisation, so an agent sees exactly what its token permits and
  there is no second credential path to secure.
- **Specification-bound.** Tools are generated from the OpenAPI document, so an
  agent cannot invent an endpoint or call one that is not published.
- **No half-formed requests.** Missing path parameters are reported before any
  call is attempted.

Treat the token as a password. It grants the same access as the REST API.

**Tool results enter the agent's context, and therefore the model provider's.**
`payout_api_read` returns real records, including customer names, emails and
addresses. Use sandbox credentials while evaluating, and decide deliberately
before pointing an agent at production data.

## Known gaps

The specification behind these tools is being reconciled with the API. Two
differences are known and worth expecting while this is in Beta:

- **Responses carry more than the schema shows.** A checkout also returns
  `billing_address`, `shipping_address`, `products`, `payment`, `all_payments`,
  `payment_token` and `is_status_final`, and the customer object carries `phone`,
  `name` and `note`. None of these are in the specification yet, so an agent will
  not know to expect them.
- **List responses are untyped.** `list_checkouts` and the other list endpoints
  declare a bare object, so an agent gets no field detail for them.

An agent reads the documentation literally. Where the specification is thin or
contradicts itself, the agent will repeat that — so treat its answers about
undocumented fields as unverified.

## Scope

Read-only, deliberately. The specification behind these tools currently
describes a subset of the routes the API serves, and a write tool over a partly
unverified surface is not something to put in front of a payments API.

The split is by HTTP method rather than per endpoint, so `payout_api_write` can
be added without reshaping anything — a client that wants reads only can then
simply leave it disabled.

Planned, in order:

1. **Durable credentials.** Accept `client_id` and `client_secret` directly, so
   the server mints and renews tokens itself and nothing expires under the
   client. This is the most disruptive gap today.
2. Reconcile the specification with the router, so coverage is complete
3. `payout_api_write` for `POST`, `PATCH`, `PUT` and `DELETE`
4. OAuth with revocable sessions, managed from the merchant account
5. The remaining APIs — Banklink, PSD2, Intel, PayoutID

Feedback: [tech@payout.one](mailto:tech@payout.one).

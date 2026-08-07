#!/usr/bin/env node
/**
 * Payout MCP server.
 *
 * Exposes the Payout API to agents in two ways:
 *   - lookup: what endpoints exist, what they take, what they return
 *   - calls:  actually invoke them
 *
 * Everything is derived from the OpenAPI specs in ../docs/openapi, so the tools
 * cannot drift from the documentation -- regenerate the specs and the agent
 * surface follows.
 *
 * Safety posture, because this is a payments API:
 *   - Sandbox is the default and only target unless production is explicitly
 *     unlocked with PAYOUT_ALLOW_PRODUCTION=true.
 *   - Credentials come from the environment and are never returned in a tool
 *     result, echoed in errors, or written to the transcript.
 *   - call_api refuses any operation not present in the spec.
 */

import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { parse as parseYaml } from "yaml";
import { z } from "zod";

const HERE = dirname(fileURLToPath(import.meta.url));
const SPEC_DIR = process.env.PAYOUT_SPEC_DIR || join(HERE, "..", "docs", "openapi");

const ENVIRONMENTS = {
  sandbox: "https://sandbox.payout.one",
  production: "https://app.payout.one",
};

const ALLOW_PRODUCTION = process.env.PAYOUT_ALLOW_PRODUCTION === "true";
const DEFAULT_ENV = process.env.PAYOUT_ENV || "sandbox";

// ---------------------------------------------------------------- specs

function loadSpecs() {
  const specs = new Map();
  let files = [];
  try {
    files = readdirSync(SPEC_DIR).filter((f) => /\.ya?ml$/.test(f));
  } catch {
    throw new Error(
      `No OpenAPI specs found at ${SPEC_DIR}. Run "make spec" in the developers repo first.`
    );
  }
  for (const f of files) {
    const slug = f.replace(/\.ya?ml$/, "");
    specs.set(slug, parseYaml(readFileSync(join(SPEC_DIR, f), "utf8")));
  }
  if (specs.size === 0) throw new Error(`No specs in ${SPEC_DIR}.`);
  return specs;
}

const SPECS = loadSpecs();

/** Flatten every spec into a single operation index. */
function indexOperations() {
  const ops = [];
  for (const [api, spec] of SPECS) {
    for (const [path, methods] of Object.entries(spec.paths || {})) {
      for (const [method, op] of Object.entries(methods)) {
        ops.push({
          api,
          method: method.toUpperCase(),
          path,
          operationId: op.operationId,
          summary: op.summary || "",
          description: op.description || "",
          tags: op.tags || [],
          op,
        });
      }
    }
  }
  return ops;
}

const OPERATIONS = indexOperations();

function findOperation(api, operationId) {
  return OPERATIONS.find(
    (o) => o.api === api && o.operationId === operationId
  );
}

/** Inline $refs one level so an agent sees the real shape, not a pointer. */
function resolveRefs(node, spec, depth = 0) {
  if (depth > 6 || node === null || typeof node !== "object") return node;
  if (Array.isArray(node)) return node.map((n) => resolveRefs(n, spec, depth + 1));
  if (typeof node.$ref === "string" && node.$ref.startsWith("#/")) {
    const target = node.$ref
      .slice(2)
      .split("/")
      .reduce((acc, k) => (acc || {})[k], spec);
    return resolveRefs(target, spec, depth + 1);
  }
  const out = {};
  for (const [k, v] of Object.entries(node)) out[k] = resolveRefs(v, spec, depth + 1);
  return out;
}

const ok = (data) => ({
  content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});
const fail = (message) => ({
  isError: true,
  content: [{ type: "text", text: message }],
});

// ---------------------------------------------------------------- auth

const tokenCache = new Map(); // env -> { token, expires }

async function getToken(env) {
  const cached = tokenCache.get(env);
  if (cached && cached.expires > Date.now() + 30_000) return cached.token;

  const id = process.env.PAYOUT_CLIENT_ID;
  const secret = process.env.PAYOUT_CLIENT_SECRET;
  if (!id || !secret) {
    throw new Error(
      "PAYOUT_CLIENT_ID and PAYOUT_CLIENT_SECRET must be set to call the API. " +
        "Lookup tools work without them."
    );
  }

  const res = await fetch(`${ENVIRONMENTS[env]}/api/v1/authorize`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ client_id: id, client_secret: secret }),
  });
  if (!res.ok) {
    // Deliberately does not include the response body -- it can echo credentials.
    throw new Error(`Authorization failed against ${env} (HTTP ${res.status}).`);
  }
  const body = await res.json();
  const token = body.token || body.access_token;
  if (!token) throw new Error("Authorization response contained no token.");

  tokenCache.set(env, { token, expires: Date.now() + 30 * 60_000 });
  return token;
}

// ---------------------------------------------------------------- server

const server = new McpServer({ name: "payout", version: "0.1.0" });

server.registerTool(
  "list_endpoints",
  {
    description:
      "List Payout API endpoints. Use this first to discover what exists. " +
      "Optionally filter by API (payment, intel, psd2, banklink, payout-id) or a search term.",
    inputSchema: {
      api: z.string().optional().describe("Restrict to one API by slug."),
      search: z.string().optional().describe("Case-insensitive match on summary, path or description."),
    },
  },
  async ({ api, search }) => {
    let rows = OPERATIONS;
    if (api) rows = rows.filter((o) => o.api === api);
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((o) =>
        `${o.summary} ${o.path} ${o.description} ${o.tags.join(" ")}`.toLowerCase().includes(q)
      );
    }
    if (rows.length === 0) {
      return ok({
        matches: 0,
        available_apis: [...SPECS.keys()],
        hint: "No endpoint matched. Try list_endpoints with no arguments.",
      });
    }
    return ok({
      matches: rows.length,
      endpoints: rows.map(({ api, method, path, operationId, summary, tags }) => ({
        api,
        operationId,
        method,
        path,
        summary,
        tags,
      })),
    });
  }
);

server.registerTool(
  "get_endpoint",
  {
    description:
      "Full detail for one endpoint: parameters, request body schema, response schema and " +
      "the prose documentation. Call this before call_api so the request is shaped correctly.",
    inputSchema: {
      api: z.string().describe("API slug, e.g. \"payment\"."),
      operationId: z.string().describe("From list_endpoints."),
    },
  },
  async ({ api, operationId }) => {
    const found = findOperation(api, operationId);
    if (!found) {
      return fail(
        `No operation "${operationId}" in API "${api}". ` +
          `Use list_endpoints to see what is available.`
      );
    }
    const spec = SPECS.get(api);
    const { op } = found;
    return ok({
      api,
      operationId,
      method: found.method,
      path: found.path,
      summary: op.summary,
      description: op.description,
      servers: spec.servers,
      security: "Bearer token from the authorize endpoint.",
      parameters: resolveRefs(op.parameters || [], spec),
      requestBody: resolveRefs(op.requestBody || null, spec),
      responses: resolveRefs(op.responses || {}, spec),
    });
  }
);

server.registerTool(
  "call_api",
  {
    description:
      "Invoke a Payout endpoint. Defaults to sandbox. Production is refused unless the server " +
      "was started with PAYOUT_ALLOW_PRODUCTION=true. Requires PAYOUT_CLIENT_ID and " +
      "PAYOUT_CLIENT_SECRET in the environment.",
    inputSchema: {
      api: z.string().describe("API slug, e.g. \"payment\"."),
      operationId: z.string().describe("From list_endpoints."),
      pathParams: z.record(z.string()).optional().describe("Values for {placeholders} in the path."),
      query: z.record(z.string()).optional().describe("Query string parameters."),
      body: z.record(z.any()).optional().describe("JSON request body."),
      environment: z.enum(["sandbox", "production"]).optional().describe("Defaults to sandbox."),
    },
  },
  async ({ api, operationId, pathParams = {}, query = {}, body, environment }) => {
    const env = environment || DEFAULT_ENV;

    if (env === "production" && !ALLOW_PRODUCTION) {
      return fail(
        "Refusing to call production. This server runs sandbox-only unless started with " +
          "PAYOUT_ALLOW_PRODUCTION=true. Retry against sandbox."
      );
    }

    const found = findOperation(api, operationId);
    if (!found) {
      return fail(`No operation "${operationId}" in API "${api}".`);
    }

    // Substitute path parameters; refuse rather than send a literal {placeholder}.
    let path = found.path;
    for (const [k, v] of Object.entries(pathParams)) {
      path = path.replaceAll(`{${k}}`, encodeURIComponent(v));
    }
    const missing = [...path.matchAll(/\{(\w+)\}/g)].map((m) => m[1]);
    if (missing.length) {
      return fail(`Missing path parameter(s): ${missing.join(", ")}.`);
    }

    const url = new URL(ENVIRONMENTS[env] + path);
    for (const [k, v] of Object.entries(query)) url.searchParams.set(k, v);

    let token;
    try {
      token = await getToken(env);
    } catch (e) {
      return fail(e.message);
    }

    let res;
    try {
      res = await fetch(url, {
        method: found.method,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: body && found.method !== "GET" ? JSON.stringify(body) : undefined,
      });
    } catch (e) {
      return fail(`Request to ${env} failed: ${e.message}`);
    }

    const text = await res.text();
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }

    return ok({
      environment: env,
      request: { method: found.method, url: url.toString() },
      status: res.status,
      ok: res.ok,
      response: parsed,
    });
  }
);

// Each spec is also a resource, for agents that prefer reading the whole thing.
for (const [slug, spec] of SPECS) {
  server.registerResource(
    `spec-${slug}`,
    `payout://spec/${slug}`,
    {
      title: `${spec.info?.title || slug} — OpenAPI`,
      description: `OpenAPI 3.1 specification for the ${slug} API.`,
      mimeType: "application/json",
    },
    async (uri) => ({
      contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(spec, null, 2) }],
    })
  );
}

const transport = new StdioServerTransport();
await server.connect(transport);

// stderr only -- stdout is the MCP transport.
console.error(
  `payout-mcp ready — ${OPERATIONS.length} operations across ${SPECS.size} APIs ` +
    `(${ALLOW_PRODUCTION ? "production unlocked" : "sandbox only"})`
);

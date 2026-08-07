#!/usr/bin/env python3
"""
Convert a Postman collection into an OpenAPI 3.1 specification.

The interesting part is not the paths -- it is the parameter tables. The Postman
docs describe request and response bodies as markdown tables inside the prose:

    | Name | Type | Max length | Required | Default | Description | Example |
    | `amount` | integer | | **yes** | | Amount in cents | `1050` |

Those are lifted into real OpenAPI schemas, so downstream consumers (Scalar,
the MCP server) get typed, expandable schemas instead of a wall of markdown.
Tables that become schemas are removed from the description to avoid stating
the same thing twice.

  venv/bin/python collection-to-openapi.py <collection.json> <out.yaml> \
      [--title "Payment API"] [--version 1.0.0]
"""

import json
import re
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------- helpers

TABLE_RE = re.compile(
    r"(^\|[^\n]*\|[ \t]*\n\|[\s:\-|]+\|[ \t]*\n(?:\|[^\n]*\|[ \t]*\n?)+)", re.M
)


def text_of(x):
    return (x.get("content", "") if isinstance(x, dict) else x) or ""


def cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def unbacktick(s):
    return s.strip().strip("`").strip()


def clean_example(s):
    """
    Example cells are written as `"John"` -- backticks for code formatting, and
    the quotes are part of the markdown, not the value. Stripping only the
    backticks leaves a value that renders as "\"John\"". Some cells are also
    unbalanced (`"customer@payout.one` with no closing quote), so trim a leading
    or trailing quote independently rather than only matched pairs.
    """
    v = unbacktick(s)
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v[:1] in "\"'":
        v = v[1:]
    if v[-1:] in "\"'":
        v = v[:-1]
    return v


def parse_table(block):
    rows = [r for r in block.strip().split("\n") if r.strip()]
    header = cells(rows[0])
    out = []
    for r in rows[2:]:
        c = cells(r)
        if len(c) < len(header):
            c += [""] * (len(header) - len(c))
        out.append(dict(zip(header, c[: len(header)])))
    return header, out


TYPE_MAP = {
    "integer": "integer",
    "int": "integer",
    "number": "number",
    "float": "number",
    "string": "string",
    "bool": "boolean",
    "boolean": "boolean",
    "json": "object",
    "object": "object",
    "array": "array",
}

# Table columns vary between the request and response tables; accept either.
NAME_KEYS = ("Name", "Argument", "Attribute", "Field")
DESC_KEYS = ("Description",)


def pick(row, keys):
    for k in keys:
        for actual in row:
            if actual.strip().lower() == k.lower():
                return row[actual]
    return ""


def row_to_property(row, schemas):
    """One table row -> (name, schema fragment, required?)."""
    name = unbacktick(pick(row, NAME_KEYS))
    if not name or name.startswith("-"):
        return None

    raw_type = unbacktick(pick(row, ("Type",))).lower()
    desc = pick(row, DESC_KEYS).strip()
    example = clean_example(pick(row, ("Example",)))
    maxlen = unbacktick(pick(row, ("Max length", "MaxLength")))
    default = unbacktick(pick(row, ("Default",)))

    # "Required" column, or the Required/Optional column used by some tables.
    req_raw = (pick(row, ("Required",)) or pick(row, ("Required/Optional",))).lower()
    required = "yes" in req_raw or "required" in req_raw

    # A capitalised type that is not a primitive refers to a nested object
    # documented by its own table further down (Customer, Payment, ...).
    prop = {}
    ref_name = unbacktick(pick(row, ("Type",)))
    if raw_type in TYPE_MAP:
        prop["type"] = TYPE_MAP[raw_type]
    elif ref_name and ref_name[:1].isupper():
        schemas.setdefault(ref_name, None)  # filled in when its table is parsed
        prop["$ref"] = f"#/components/schemas/{ref_name}"
    elif raw_type:
        prop["type"] = "string"
    else:
        prop["type"] = "string"

    if desc:
        prop["description"] = desc
    if example and "$ref" not in prop:
        prop["example"] = coerce(example, prop.get("type"))
    if maxlen.isdigit() and prop.get("type") == "string":
        prop["maxLength"] = int(maxlen)
    if default and "$ref" not in prop:
        prop["default"] = coerce(default, prop.get("type"))

    return name, prop, required


def coerce(v, t):
    if t == "integer":
        try:
            return int(v)
        except ValueError:
            return v
    if t == "number":
        try:
            return float(v)
        except ValueError:
            return v
    if t == "boolean":
        return v.lower() in ("true", "yes")
    if t in ("object", "array"):
        try:
            return json.loads(v)
        except (ValueError, TypeError):
            return v
    return v


def merge_schema(existing, new):
    """
    The same object is documented more than once -- e.g. Customer appears under
    both the request and the response tables, and only the request form carries
    a Required column. Keep the richer definition rather than letting whichever
    table is parsed last win.
    """
    if not existing:
        return new
    if not new:
        return existing
    merged = {"type": "object", "properties": dict(existing.get("properties", {}))}
    for name, prop in new.get("properties", {}).items():
        cur = merged["properties"].get(name)
        # More keys == more information (maxLength, example, default, ...).
        if not cur or len(prop) > len(cur):
            merged["properties"][name] = prop
    required = sorted(set(existing.get("required", [])) | set(new.get("required", [])))
    if required:
        merged["required"] = required
    return merged


def table_to_schema(block, schemas):
    header, rows = parse_table(block)
    if not any(k.lower() in [h.lower() for h in header] for k in NAME_KEYS):
        return None  # not a parameter table (e.g. the webhook event list)
    props, required = {}, []
    for r in rows:
        got = row_to_property(r, schemas)
        if not got:
            continue
        name, prop, is_req = got
        props[name] = prop
        if is_req:
            required.append(name)
    if not props:
        return None
    schema = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def hoist_sections(desc):
    """
    The authentication and error documentation is buried inside the Authorize
    endpoint's description, where a reader looking for "how do I authenticate"
    will not find it. Lift those blocks out so they can be rendered as
    top-level sections, the way Stripe does.

    Returns (remaining_prose, {"authentication": md, "errors": md}).
    """
    sections = {}
    lines = desc.split("\n")

    # Index every heading with its level and line number.
    heads = []
    for i, l in enumerate(lines):
        m = re.match(r"^(#{1,6})\s*(.+?)\s*$", l)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
        # Setext-style: a line underlined with === or ---
        elif i and re.match(r"^=+\s*$", l) and lines[i - 1].strip():
            heads.append((i - 1, 1, lines[i - 1].strip()))

    WANTED = {
        "authentication": ("authentification", "authentication", "authorization"),
        "errors": ("errors", "error codes", "error"),
    }

    taken = set()
    for key, needles in WANTED.items():
        for idx, (ln, level, title) in enumerate(heads):
            if title.strip().lower() not in needles:
                continue
            # Section runs to the next heading of the same or higher level.
            end = len(lines)
            for ln2, level2, _ in heads[idx + 1 :]:
                if level2 <= level:
                    end = ln2
                    break
            start = ln
            body = "\n".join(lines[start:end]).strip()
            # Drop the setext underline if it came through.
            body = re.sub(r"^(.+)\n=+\s*$", r"# \1", body, count=1, flags=re.M)
            if not body.startswith("#"):
                body = f"# {title}\n" + body
            if body and key not in sections:
                sections[key] = body
                taken.update(range(start, end))
            break

    remaining = "\n".join(l for i, l in enumerate(lines) if i not in taken)
    return re.sub(r"\n{3,}", "\n\n", remaining).strip(), sections


def heading_before(desc, idx):
    """Nearest markdown heading above a character offset."""
    head = None
    for m in re.finditer(r"^(#{1,6})\s*(.+)$", desc[:idx], re.M):
        head = m.group(2).strip()
    return head or ""


def split_description(desc, schemas):
    """Pull schema tables out of the prose. Returns (prose, request, response)."""
    request = response = None
    consumed = []

    for m in TABLE_RE.finditer(desc):
        block = m.group(1)
        head = heading_before(desc, m.start()).lower()
        schema = table_to_schema(block, schemas)
        if schema is None:
            continue

        if "customer attributes" in head:
            schemas["Customer"] = merge_schema(schemas.get("Customer"), schema)
            consumed.append(m.span())
        elif "payment attributes" in head:
            schemas["Payment"] = merge_schema(schemas.get("Payment"), schema)
            consumed.append(m.span())
        elif "request body" in head or head.startswith("arguments"):
            request = schema
            consumed.append(m.span())
        elif "response body" in head:
            response = schema
            consumed.append(m.span())

    # Remove consumed tables (and the heading immediately above them) so the
    # rendered prose does not repeat what the schema already shows.
    out = desc
    for start, end in sorted(consumed, reverse=True):
        head_start = out.rfind("\n#", 0, start)
        cut = head_start if head_start != -1 and start - head_start < 400 else start
        out = out[:cut] + out[end:]

    return re.sub(r"\n{3,}", "\n\n", out).strip(), request, response


# ---------------------------------------------------------------- paths

VAR_RE = re.compile(r"\{\{(\w+)\}\}")


def normalise_path(raw):
    """Postman URL -> OpenAPI path + the path parameters it declares."""
    p = re.sub(r"^\{\{[^}]+\}\}://\{\{[^}]+\}\}", "", raw)
    p = re.sub(r"^https?://[^/]+", "", p)
    p = p.split("?")[0]

    # Some collections use a single {{baseUrl}} variable with no scheme, which
    # leaves a leading host segment behind. An OpenAPI path must start with "/".
    p = re.sub(r"^\{\{[^}]+\}\}", "", p)
    if p and not p.startswith("/"):
        p = "/" + p.split("/", 1)[-1] if "/" in p else "/"

    params = []

    def colon(m):
        params.append(m.group(1))
        return "{" + m.group(1) + "}"

    p = re.sub(r":(\w+)", colon, p)

    def curly(m):
        params.append(m.group(1))
        return "{" + m.group(1) + "}"

    p = VAR_RE.sub(curly, p)
    return p or "/", params


def build(coll, title, version):
    info_src = coll.get("info") or {}
    schemas = {}
    paths = {}
    hoisted = {}

    def walk(items, folder=None):
        for it in items or []:
            if "item" in it:
                yield from walk(it["item"], it.get("name"))
            else:
                yield it, folder

    for it, folder in walk(coll.get("item")):
        r = it.get("request") or {}
        url = r.get("url")
        raw = url.get("raw", "") if isinstance(url, dict) else (url or "")
        path, path_params = normalise_path(raw)
        method = (r.get("method") or "GET").lower()

        # Webhook examples describe an endpoint the merchant implements, not
        # one we serve. They do not belong in this spec's paths.
        if "your-notification-url" in raw or "your_notification" in raw:
            continue

        prose, req_schema, resp_schema = split_description(
            text_of(r.get("description")), schemas
        )
        prose, found = hoist_sections(prose)
        for k, v in found.items():
            hoisted.setdefault(k, v)

        op = {
            "summary": it.get("name", "").strip(),
            "operationId": re.sub(r"\W+", "_", it.get("name", "")).strip("_").lower(),
        }
        if folder:
            op["tags"] = [folder]
        if prose:
            op["description"] = prose

        params = []
        for name in dict.fromkeys(path_params):
            params.append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            )
        if isinstance(url, dict):
            for q in url.get("query") or []:
                if q.get("disabled"):
                    continue
                params.append(
                    {
                        "name": q.get("key"),
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        **({"description": q["description"]} if q.get("description") else {}),
                    }
                )
        if params:
            op["parameters"] = params

        body = r.get("body") or {}
        if body.get("mode") == "raw" and body.get("raw", "").strip():
            content = {"schema": req_schema or {"type": "object"}}
            try:
                content["example"] = json.loads(body["raw"])
            except (ValueError, TypeError):
                pass
            op["requestBody"] = {"required": True, "content": {"application/json": content}}

        op["responses"] = {
            "200": {
                "description": "Success",
                "content": {
                    "application/json": {"schema": resp_schema or {"type": "object"}}
                },
            },
            "401": {"description": "Missing or invalid bearer token"},
        }

        paths.setdefault(path, {})[method] = op

    # A capitalised Type column produces a $ref, but only some of those objects
    # have a table of their own (Customer does; UUID does not). Resolve the
    # danglers to primitives rather than emitting an unresolvable reference.
    PRIMITIVE_FALLBACK = {
        "uuid": {"type": "string", "format": "uuid"},
        "datetime": {"type": "string", "format": "date-time"},
        "date": {"type": "string", "format": "date"},
        "url": {"type": "string", "format": "uri"},
        "email": {"type": "string", "format": "email"},
    }
    defined = {k for k, v in schemas.items() if v}
    dangling = []

    def resolve(node):
        if isinstance(node, dict):
            ref = node.get("$ref", "")
            if ref.startswith("#/components/schemas/"):
                name = ref.rsplit("/", 1)[-1]
                if name not in defined:
                    dangling.append(name)
                    node.pop("$ref")
                    node.update(
                        PRIMITIVE_FALLBACK.get(name.lower(), {"type": "string"})
                    )
                    return
            for v in node.values():
                resolve(v)
        elif isinstance(node, list):
            for v in node:
                resolve(v)

    resolve(paths)
    resolve({k: v for k, v in schemas.items() if v})
    if dangling:
        print(f"  resolved {len(dangling)} undefined type(s) to primitives: "
              f"{', '.join(sorted(set(dangling)))}")

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "description": text_of(info_src.get("description")).strip(),
        },
        "servers": [
            {"url": "https://app.payout.one", "description": "Production"},
            {"url": "https://sandbox.payout.one", "description": "Sandbox"},
        ],
        "security": [{"bearerAuth": []}],
        # Rendered as standalone sections above the operations.
        "x-sections": hoisted,
        "paths": paths,
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Token from POST /api/v1/authorize.",
                }
            },
            "schemas": {k: v for k, v in schemas.items() if v},
        },
    }
    return spec


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    title = "Payment API"
    version = "1.0.0"
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    if "--version" in sys.argv:
        version = sys.argv[sys.argv.index("--version") + 1]

    spec = build(json.loads(Path(src).read_text()), title, version)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=100))

    n_ops = sum(len(v) for v in spec["paths"].values())
    print(
        f"wrote {out}: {len(spec['paths'])} paths, {n_ops} operations, "
        f"{len(spec['components']['schemas'])} schemas"
    )

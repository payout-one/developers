#!/usr/bin/env python3
"""
Unified static site: markdown guides and OpenAPI references in one design.

Renders into docs/next/ so the live docsify site is untouched -- this is a
preview to evaluate, not a cutover.

  venv/bin/python build-site.py [--docs docs] [--out docs/next]

Inputs
  docs/**/*.md        the existing guides (nav order taken from _sidebar.md)
  docs/openapi/*.yaml the generated OpenAPI specs

Outputs
  <out>/index.html            landing page
  <out>/guides/<slug>.html    one page per guide
  <out>/api/<slug>.html       one page per spec
  <out>/mcp.html              agent integration page
  <out>/search-index.json     client-side search index
"""

import html
import json
import re
import shutil
import sys
from pathlib import Path

import markdown
import yaml

MD = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "toc", "md_in_html"])


def style_code_blocks(html_text, root=""):
    """
    Give prose code blocks the same dark, labelled treatment as the reference
    pages. python-markdown emits <pre><code class="language-x">; wrap that in the
    .cb shell with a header and run it through the same highlighters.
    """
    LABELS = {
        "bash": "Command Line", "sh": "Command Line", "shell": "Command Line",
        "console": "Command Line", "json": "JSON", "toml": "TOML",
        "yaml": "YAML", "yml": "YAML", "elixir": "Elixir", "js": "JavaScript",
        "javascript": "JavaScript", "python": "Python", "php": "PHP",
        "http": "HTTP", "": "Code",
    }

    def repl(m):
        lang = (m.group("lang") or "").lower()
        raw = html.unescape(m.group("body"))
        if lang in ("bash", "sh", "shell", "console"):
            body = hl_shell(raw)
        elif lang == "json":
            body = hl_json(raw)
        elif lang in ("js", "javascript", "python", "php", "elixir", "toml", "yaml", "yml"):
            body = hl_code(raw)
        else:
            body = html.escape(raw)
        label = LABELS.get(lang, lang.upper() or "Code")
        return (
            f'<div class="cb cb-dark"><div class="cb-head">'
            f'<span class="cb-lang">{html.escape(label)}</span>'
            f'<button class="cb-copy" type="button">copy</button></div>'
            f"<pre><code>{body}</code></pre></div>"
        )

    return re.sub(
        r'<pre><code(?: class="language-(?P<lang>[\w-]+)")?>(?P<body>.*?)</code></pre>',
        repl,
        html_text,
        flags=re.S,
    )


def render_md(text, root=""):
    MD.reset()
    out = MD.convert(text or "")
    out = out.replace("<table>", '<div class="table-scroll"><table>').replace(
        "</table>", "</table></div>"
    )
    # Guides link at the live site's Scalar pages (/api/<slug>/index.html) and at
    # sibling markdown files. Inside this build those must point at the unified
    # pages instead, or the preview links back out to the old site.
    out = re.sub(
        r'href="/?api/([a-z0-9-]+)/index\.html"',
        lambda m: f'href="{root}api/{m.group(1)}.html"',
        out,
    )
    out = re.sub(
        r'href="\.?/?([A-Za-z0-9/_-]+)\.md(#[^"]*)?"',
        lambda m: f'href="{root}guides/{guide_slug(m.group(1))}.html{m.group(2) or ""}"',
        out,
    )
    return style_code_blocks(out, root)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "page"


# ---------------------------------------------------------------- nav

def parse_sidebar(path):
    """docsify _sidebar.md -> [(depth, label, target)] ; target None for headings."""
    items = []
    if not path.exists():
        return items
    for line in path.read_text().splitlines():
        m = re.match(r"^(\s*)-\s*\[([^\]]+)\]\(([^)\s]+)", line)
        if not m:
            continue
        depth = len(m.group(1)) // 2
        label, target = m.group(2).strip(), m.group(3).strip()
        items.append((depth, label, target))
    return items


def guide_slug(target):
    t = target.split("#")[0].split("?")[0].lstrip("/")
    t = re.sub(r"\.md$", "", t)
    return slugify(t) if t else "home"


# ---------------------------------------------------------------- OpenAPI

def deref(node, spec, depth=0):
    if depth > 8 or not isinstance(node, (dict, list)):
        return node
    if isinstance(node, list):
        return [deref(n, spec, depth + 1) for n in node]
    if isinstance(node.get("$ref"), str) and node["$ref"].startswith("#/"):
        tgt = spec
        for part in node["$ref"][2:].split("/"):
            tgt = (tgt or {}).get(part, {})
        return deref(tgt, spec, depth + 1)
    return {k: deref(v, spec, depth + 1) for k, v in node.items()}


# ---------------------------------------------------------------- highlight

def hl_json(text):
    """Tokenise JSON for colouring. Build-time, so no runtime JS dependency."""
    out, i = [], 0
    tok = re.compile(
        r'(?P<key>"(?:[^"\\]|\\.)*")(?P<colon>\s*:)'
        r'|(?P<str>"(?:[^"\\]|\\.)*")'
        r"|(?P<num>-?\d+\.?\d*(?:[eE][+-]?\d+)?)"
        r"|(?P<lit>\btrue\b|\bfalse\b|\bnull\b)"
        r"|(?P<var>\{\{[^}]+\}\})"
    )
    for m in tok.finditer(text):
        out.append(html.escape(text[i : m.start()]))
        if m.group("key"):
            out.append(f'<span class="t-key">{html.escape(m.group("key"))}</span>')
            out.append(html.escape(m.group("colon")))
        elif m.group("var"):
            out.append(f'<span class="t-var">{html.escape(m.group("var"))}</span>')
        elif m.group("str"):
            out.append(f'<span class="t-str">{html.escape(m.group("str"))}</span>')
        elif m.group("num"):
            out.append(f'<span class="t-num">{m.group("num")}</span>')
        else:
            out.append(f'<span class="t-lit">{m.group("lit")}</span>')
        i = m.end()
    out.append(html.escape(text[i:]))
    return "".join(out)


def hl_shell(text):
    """Colour a curl invocation: command, flags, urls, quoted strings, vars."""
    out, i = [], 0
    tok = re.compile(
        r"(?P<cmd>^\s*curl\b)"
        r"|(?P<flag>\s-{1,2}[A-Za-z-]+\b)"
        r"|(?P<url>https?://[^\s'\"\\]+)"
        r"|(?P<var>\$\w+|\{\{[^}]+\}\})"
        r"|(?P<str>'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")",
        re.M,
    )
    for m in tok.finditer(text):
        out.append(html.escape(text[i : m.start()]))
        kind = m.lastgroup
        frag = m.group(kind)
        cls = {"cmd": "t-cmd", "flag": "t-flag", "url": "t-url", "var": "t-var", "str": "t-str"}[kind]
        # A quoted JSON payload is worth highlighting as JSON, not as one string.
        if kind == "str" and frag.lstrip("'\"").lstrip().startswith("{"):
            q = frag[0]
            out.append(f'<span class="t-str">{q}</span>{hl_json(frag[1:-1])}<span class="t-str">{q}</span>')
        else:
            out.append(f'<span class="{cls}">{html.escape(frag)}</span>')
        i = m.end()
    out.append(html.escape(text[i:]))
    return "".join(out)


def hl_code(text):
    """Generic highlighter for the JS / Python / PHP samples."""
    out, i = [], 0
    tok = re.compile(
        r"(?P<cm>#[^\n]*|//[^\n]*)"
        r"|(?P<str>\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)"
        r"|(?P<kw>\b(?:const|await|async|import|from|return|true|false|null|None|True|False)\b)"
        r"|(?P<fn>\b(?:fetch|requests|json|curl_init|curl_setopt|curl_exec|getenv|environ)\b)"
        r"|(?P<num>\b\d+\b)"
        r"|(?P<var>\$\w+)"
    )
    for m in tok.finditer(text):
        out.append(html.escape(text[i:m.start()]))
        k = m.lastgroup
        cls = {"cm":"t-cm","str":"t-str","kw":"t-lit","fn":"t-cmd","num":"t-num","var":"t-var"}[k]
        out.append(f'<span class="{cls}">{html.escape(m.group(k))}</span>')
        i = m.end()
    out.append(html.escape(text[i:]))
    return "".join(out)


def code_block(text, lang, label=None):
    body = hl_json(text) if lang == "json" else hl_shell(text)
    head = f'<div class="cb-head"><span>{html.escape(label or lang)}</span></div>' if label else ""
    return f'<div class="cb cb-dark">{head}<pre><code>{body}</code></pre></div>'


def type_label(schema):
    if not isinstance(schema, dict):
        return "any"
    if "type" in schema:
        t = schema["type"]
        if t == "array":
            return f"{type_label(schema.get('items', {}))}[]"
        fmt = schema.get("format")
        return f"{t}<{fmt}>" if fmt else t
    if "properties" in schema:
        return "object"
    return "any"


def render_schema(schema, title, depth=0):
    """
    Stripe-style property list: identifier, REQUIRED flag and type on one line;
    description beneath at full width. The previous three-column grid starved
    the description to a few characters once anything nested.
    """
    if not isinstance(schema, dict):
        return ""
    props = schema.get("properties") or {}
    if not props:
        return ""
    required = set(schema.get("required") or [])
    rows = []
    for name, p in props.items():
        p = p if isinstance(p, dict) else {}
        meta = []
        if p.get("description"):
            meta.append(html.escape(str(p["description"])))
        if p.get("maxLength"):
            meta.append(f"max {p['maxLength']}")
        if "example" in p:
            ex = p["example"]
            ex = ex if isinstance(ex, str) else json.dumps(ex)
            meta.append(f'e.g. <code>{html.escape(str(ex)[:70])}</code>')

        head = (
            f'<div class="prop-head"><span class="prop-name">{html.escape(name)}</span>'
            + (' <span class="req">required</span>' if name in required else "")
            + f'<span class="prop-type">{html.escape(type_label(p))}</span></div>'
        )
        desc = f'<div class="prop-desc">{" · ".join(meta)}</div>' if meta else ""
        nested = render_schema(p, "", depth + 1) if p.get("properties") else ""
        rows.append(f'<div class="prop">{head}{desc}{nested}</div>')

    cls = "schema nested" if depth else "schema"
    head = f'<h4>{html.escape(title)}</h4>' if title else ""
    return f'<div class="{cls}">{head}{"".join(rows)}</div>'


def gen_curl(base, method, path, body):
    lines = [f"curl -X {method} {base}{path} \\", '  -H "Authorization: Bearer $TOKEN" \\']
    if body is not None:
        lines.append('  -H "Content-Type: application/json" \\')
        payload = json.dumps(body, indent=2)
        payload = "\n".join(
            ("  -d '" + l) if i == 0 else "     " + l for i, l in enumerate(payload.splitlines())
        )
        lines.append(payload + "'")
    else:
        lines[-1] = lines[-1].rstrip(" \\")
    return "\n".join(lines)


def gen_node(base, method, path, body):
    out = [
        f'const res = await fetch("{base}{path}", {{',
        f'  method: "{method}",',
        "  headers: {",
        '    Authorization: `Bearer ${process.env.PAYOUT_TOKEN}`,',
    ]
    if body is not None:
        out.append('    "Content-Type": "application/json",')
    out.append("  },")
    if body is not None:
        payload = json.dumps(body, indent=2)
        payload = "\n".join(("  body: JSON.stringify(" + l) if i == 0 else "  " + l
                            for i, l in enumerate(payload.splitlines()))
        out.append(payload + "),")
    out.append("});")
    out.append("const data = await res.json();")
    return "\n".join(out)


def gen_python(base, method, path, body):
    out = ["import os, requests", "", f'res = requests.{method.lower()}(', f'    "{base}{path}",',
           '    headers={"Authorization": f"Bearer {os.environ[\'PAYOUT_TOKEN\']}"},']
    if body is not None:
        payload = json.dumps(body, indent=4)
        payload = "\n".join(("    json=" + l) if i == 0 else "    " + l
                            for i, l in enumerate(payload.splitlines()))
        out.append(payload + ",")
    out += [")", "data = res.json()"]
    return "\n".join(out)


def gen_php(base, method, path, body):
    out = ["<?php", "$ch = curl_init();",
           f'curl_setopt($ch, CURLOPT_URL, "{base}{path}");',
           "curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);",
           f'curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "{method}");']
    headers = ['"Authorization: Bearer " . getenv("PAYOUT_TOKEN")']
    if body is not None:
        headers.append('"Content-Type: application/json"')
        out.append(
            "curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode("
            + json.dumps(body, indent=2).replace("{", "[").replace("}", "]").replace('":', '" =>')
            + "));"
        )
    out.append("curl_setopt($ch, CURLOPT_HTTPHEADER, [" + ", ".join(headers) + "]);")
    out += ["$data = json_decode(curl_exec($ch), true);", "curl_close($ch);"]
    return "\n".join(out)


LANGS = [
    ("curl", "cURL", gen_curl, "shell"),
    ("node", "Node.js", gen_node, "js"),
    ("python", "Python", gen_python, "python"),
    ("php", "PHP", gen_php, "php"),
]


def op_markdown(spec_title, m, path, op, body_schema, ok_schema, req_example, base):
    """A section rendered as markdown, for 'Copy for LLM' and the .md view."""
    out = [f"## {op.get('summary') or ''}".rstrip(), "", f"`{m} {path}`", ""]
    if op.get("description"):
        out += [op["description"].strip(), ""]

    def props_md(schema, heading, indent=0):
        if not isinstance(schema, dict) or not schema.get("properties"):
            return []
        req = set(schema.get("required") or [])
        rows = [f"### {heading}", ""] if heading else []
        for name, p in schema["properties"].items():
            p = p if isinstance(p, dict) else {}
            flag = " (required)" if name in req else ""
            bits = [type_label(p) + flag]
            if p.get("description"):
                bits.append(str(p["description"]))
            if "example" in p:
                bits.append(f"e.g. {p['example']}")
            rows.append("  " * indent + f"- `{name}` — " + " · ".join(bits))
            if p.get("properties"):
                rows += props_md(p, "", indent + 1)
        return rows + [""]

    out += props_md(body_schema, "Request body")
    out += props_md(ok_schema, "Response")
    out += ["### Example", "", "```bash", gen_curl(base, m, path, req_example), "```", ""]
    return "\n".join(out)


def schema_example(schema, depth=0):
    """Synthesise a response example from the schema's declared examples."""
    if not isinstance(schema, dict) or depth > 4:
        return None
    props = schema.get("properties") or {}
    if not props:
        return None
    out = {}
    for name, p in props.items():
        if not isinstance(p, dict):
            continue
        if "example" in p:
            out[name] = p["example"]
        elif p.get("properties"):
            nested = schema_example(p, depth + 1)
            if nested:
                out[name] = nested
        elif p.get("type") == "array":
            out[name] = []
    return out or None


def curl_example(base, method, path, body):
    lines = [f"curl -X {method} {base}{path} \\", '  -H "Authorization: Bearer $TOKEN" \\']
    if body is not None:
        lines.append('  -H "Content-Type: application/json" \\')
        payload = json.dumps(body, indent=2)
        payload = "\n".join(
            ("  -d '" + l) if i == 0 else "     " + l for i, l in enumerate(payload.splitlines())
        )
        lines.append(payload + "'")
    else:
        lines[-1] = lines[-1].rstrip(" \\")
    return "\n".join(lines)


TOOLBAR = (
    '<div class="sec-tools">'
    '<button class="sec-btn copy-md" type="button" title="Copy this section as markdown">'
    'Copy for LLM</button>'
    '<a class="sec-btn" href="../md/{slug}.md">View as Markdown</a>'
    '<a class="sec-btn" href="../openapi/{slug}.yaml">Spec</a>'
    "</div>"
)


def render_spec(spec, slug):
    info = spec.get("info") or {}
    md_all = []
    base = (spec.get("servers") or [{}])[0].get("url", "")
    nav, search = [], []
    out = [f'<section class="intro"><div class="inner"><div class="prose">'
           f'{render_md(info.get("description", ""), "../")}</div></div></section>']

    # Authentication and Errors were buried inside the first endpoint; the
    # converter hoists them so they can lead the page, as Stripe does.
    for key, title in (("authentication", "Authentication"), ("errors", "Errors")):
        block = (spec.get("x-sections") or {}).get(key)
        if not block:
            continue
        sid = slugify(title)
        nav.append((sid, "", title))
        search.append({"kind": f"{slug} api", "title": title,
                       "ctx": "authentication and errors", "url": f"api/{slug}.html#{sid}"})
        out.append(
            f'<section class="op" id="{sid}" data-md="{html.escape(block, quote=True)}">'
            f'<div class="inner"><div class="op-head"><h2>{title}</h2>'
            f'{TOOLBAR.format(slug=slug)}</div>'
            f'<div class="op-grid stacked"><div class="prose">{render_md(block, "../")}</div></div>'
            f"</div></section>"
        )
    nav, search = [], []

    for path, methods in (spec.get("paths") or {}).items():
        for method, op in methods.items():
            m = method.upper()
            oid = op.get("operationId") or slugify(f"{m}-{path}")
            summary = op.get("summary") or oid
            nav.append((oid, m, summary))
            search.append(
                {
                    "kind": f"{slug} api",
                    "title": summary,
                    "ctx": f"{m} {path}",
                    "url": f"api/{slug}.html#{oid}",
                }
            )

            body_schema = req_example = None
            rb = deref(op.get("requestBody") or {}, spec)
            if rb:
                content = (rb.get("content") or {}).get("application/json") or {}
                body_schema = content.get("schema")
                req_example = content.get("example")

            resp = deref(op.get("responses") or {}, spec)
            ok_schema = (
                ((resp.get("200") or {}).get("content") or {}).get("application/json") or {}
            ).get("schema")

            params = deref(op.get("parameters") or [], spec)
            param_html = ""
            if params:
                rows = "".join(
                    f'<div class="prop"><span class="prop-name">{html.escape(p.get("name",""))}'
                    + (' <span class="req">required</span>' if p.get("required") else "")
                    + f'</span><span class="prop-type">{html.escape(p.get("in",""))}</span>'
                    + f'<span class="prop-meta">{html.escape(p.get("description",""))}</span></div>'
                    for p in params
                )
                param_html = f'<div class="schema"><h4>Parameters</h4>{rows}</div>'

            left = [f'<div class="prose">{render_md(op.get("description",""))}</div>', param_html]
            if body_schema:
                left.append(render_schema(body_schema, "Request body"))
            if ok_schema:
                left.append(render_schema(ok_schema, "Response"))

            # The curl invocation already contains the request body, so printing
            # the same JSON again underneath is pure duplication. Show the call,
            # then the thing you cannot see from it -- the response.
            tabs, panes = [], []
            for i, (key, label, fn, lang) in enumerate(LANGS):
                on = " on" if i == 0 else ""
                tabs.append(f'<button class="lang{on}" data-lang="{key}" type="button">{label}</button>')
                hidden = "" if i == 0 else " hidden"
                panes.append(
                    f'<div class="lang-pane" data-lang="{key}"{hidden}>'
                    f'<pre><code>{hl_shell(fn(base, m, path, req_example)) if lang == "shell" else hl_code(fn(base, m, path, req_example))}</code></pre>'
                    f"</div>"
                )
            right = [
                '<div class="cb cb-dark"><div class="cb-head"><span>Request</span>'
                f'<div class="langs">{"".join(tabs)}</div></div>{"".join(panes)}</div>'
            ]
            resp_example = schema_example(ok_schema)
            if resp_example:
                right.append(code_block(json.dumps(resp_example, indent=2), "json", "Response"))

            stacked = "" if (body_schema or ok_schema or params) else " stacked"
            md = op_markdown(slug, m, path, op, body_schema, ok_schema, req_example, base)
            md_all.append(md)
            out.append(
                f'<section class="op" id="{oid}" data-md="{html.escape(md, quote=True)}"><div class="inner">'
                f'<div class="op-head"><span class="verb {method}">{m}</span>'
                f'<h2>{html.escape(summary)}</h2>'
                f'{TOOLBAR.format(slug=slug)}'
                f"</div>"
                f'<div class="op-path">{html.escape(path)}</div>'
                f'<div class="op-grid{stacked}"><div>{"".join(left)}</div>'
                f'<div class="panel">{"".join(right)}</div></div>'
                f"</div></section>"
            )

    toc = "".join(
        f'<a href="#{oid}"><span class="m">{m}</span>{html.escape(s)}</a>'
        for oid, m, s in nav
    )
    return "".join(out), toc, search, "\n\n".join(md_all)


# ---------------------------------------------------------------- build

def page(shell, *, title, eyebrow, body, sidenav, topnav, root, md_link, desc, footer):
    return (
        shell.replace("{{TITLE}}", html.escape(title))
        .replace("{{EYEBROW}}", html.escape(eyebrow))
        .replace("{{BODY}}", body)
        .replace("{{SIDENAV}}", sidenav)
        .replace("{{TOPNAV}}", topnav)
        .replace("{{ROOT}}", root)
        .replace("{{MD}}", md_link)
        .replace("{{DESC}}", html.escape(desc))
        .replace("{{FOOTER}}", footer)
    )


def main():
    argv = sys.argv[1:]
    docs = Path(argv[argv.index("--docs") + 1] if "--docs" in argv else "docs")
    out = Path(argv[argv.index("--out") + 1] if "--out" in argv else "docs/next")

    shell = Path(__file__).with_name("site-shell.html").read_text()
    if out.exists():
        shutil.rmtree(out)
    (out / "guides").mkdir(parents=True)
    (out / "api").mkdir(parents=True)

    specs = {}
    for f in sorted((docs / "openapi").glob("*.yaml")):
        specs[f.stem] = yaml.safe_load(f.read_text())

    # Ship the specs inside the site: the reference pages link to them, and an
    # agent fetching ../openapi/<slug>.yaml must get a file, not a 404.
    (out / "openapi").mkdir(parents=True, exist_ok=True)
    for f in sorted((docs / "openapi").glob("*.yaml")):
        shutil.copy2(f, out / "openapi" / f.name)

    (out / "md").mkdir(parents=True, exist_ok=True)
    for f in sorted(docs.rglob("*.md")):
        if f.name.startswith("_") or "next" in f.parts:
            continue
        rel_md = f.relative_to(docs).as_posix()
        shutil.copy2(f, out / "md" / (guide_slug(rel_md) + ".md"))
        if rel_md.lower() == "readme.md":
            shutil.copy2(f, out / "md" / "home.md")

    sidebar = parse_sidebar(docs / "_sidebar.md")
    search = []

    # --- navigation --------------------------------------------------------
    def api_links_for(active=None, ops_html=""):
        out = []
        for s, sp in specs.items():
            title = html.escape((sp.get("info") or {}).get("title", s))
            cur = ' aria-current="page"' if s == active else ""
            out.append(f'<li><a href="{{{{ROOT}}}}api/{s}.html"{cur}>{title}</a></li>')
            if s == active and ops_html:
                out.append(f'<li><div class="ops">{ops_html}</div></li>')
        return "".join(out)

    api_links = api_links_for()
    guide_links = []
    for depth, label, target in sidebar:
        if target.startswith(("/api/", "/next/", "http")):
            continue
        cls = ' class="sub"' if depth else ""
        guide_links.append(
            f'<li{cls}><a href="{{{{ROOT}}}}guides/{guide_slug(target)}.html">{html.escape(label)}</a></li>'
        )
    def build_sidenav(active=None, ops_html=""):
        return (
            f"<h3>API reference</h3><ul>{api_links_for(active, ops_html)}</ul>"
            "<h3>Agents</h3><ul><li><a href=\"{{ROOT}}mcp.html\">MCP server</a></li></ul>"
            f"<h3>Guides</h3><ul>{''.join(guide_links)}</ul>"
        )

    sidenav = (
        f"<h3>API reference</h3><ul>{api_links}</ul>"
        "<h3>Agents</h3><ul><li><a href=\"{{ROOT}}mcp.html\">MCP server</a></li></ul>"
        f"<h3>Guides</h3><ul>{''.join(guide_links)}</ul>"
    )
    topnav = (
        "<a href='{{ROOT}}index.html'>Overview</a>"
        "<a href='{{ROOT}}api/payment.html'>API</a>"
        "<a href='{{ROOT}}mcp.html'>MCP</a>"
    )
    footer = (
        "Generated from the OpenAPI specs and the existing guides. "
        "Preview build — the live site is unchanged."
    )

    def write(rel, *, title, eyebrow, body, desc, md_link="", nav=None):
        depth = len(Path(rel).parts) - 1
        root = "../" * depth
        nav = nav if nav is not None else sidenav
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            page(
                shell,
                title=title,
                eyebrow=eyebrow,
                body=body,
                sidenav=nav.replace("{{ROOT}}", root),
                topnav=topnav.replace("{{ROOT}}", root),
                root=root,
                md_link=md_link,
                desc=desc,
                footer=footer,
            )
        )

    # --- API reference pages ----------------------------------------------
    for slug, spec in specs.items():
        body, toc, s, md_doc = render_spec(spec, slug)
        (out / "md").mkdir(exist_ok=True)
        (out / "md" / f"{slug}.md").write_text(
            f"# {(spec.get('info') or {}).get('title', slug)}\n\n{md_doc}\n"
        )
        search += s
        title = (spec.get("info") or {}).get("title", slug)
        write(
            f"api/{slug}.html",
            title=title,
            eyebrow="API reference",
            body=body,
            desc=f"{title} reference.",
            md_link=f"../openapi/{slug}.yaml",
            nav=build_sidenav(slug, toc),
        )

    # --- guides ------------------------------------------------------------
    seen = set()
    for depth, label, target in sidebar:
        if target.startswith(("/api/", "/next/", "http")):
            continue
        src = docs / (target.split("#")[0].lstrip("/") or "README.md")
        if src.suffix != ".md":
            src = src.with_suffix(".md")
        slug = guide_slug(target)
        if slug in seen or not src.exists():
            continue
        seen.add(slug)
        text = src.read_text()
        write(
            f"guides/{slug}.html",
            title=label,
            eyebrow="Guide",
            body=f'<div class="prose">{render_md(text, "../")}</div>',
            desc=f"{label} — Payout developer guide.",
            md_link=f"../md/{slug}.md",
        )
        search.append(
            {
                "kind": "guide",
                "title": label,
                "ctx": re.sub(r"[#*`>\[\]()]", "", text)[:110].replace("\n", " ").strip(),
                "url": f"guides/{slug}.html",
            }
        )

    # Guides reachable only by cross-link (not in _sidebar.md) still need pages,
    # otherwise those links dead-end.
    for src in sorted(docs.rglob("*.md")):
        if src.name.startswith("_") or "next" in src.parts:
            continue
        rel = src.relative_to(docs).as_posix()
        slug = guide_slug(rel)
        if slug in seen:
            continue
        seen.add(slug)
        text = src.read_text()
        title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("#")), slug)
        write(
            f"guides/{slug}.html",
            title=title,
            eyebrow="Guide",
            body=f'<div class="prose">{render_md(text, "../")}</div>',
            desc=f"{title} — Payout developer guide.",
            md_link=f"../md/{slug}.md",
        )
        search.append({"kind": "guide", "title": title,
                       "ctx": re.sub(r"[#*`>\[\]()]", "", text)[:110].replace("\n", " ").strip(),
                       "url": f"guides/{slug}.html"})

    # --- MCP page ----------------------------------------------------------
    mcp_md = Path(__file__).with_name("mcp-page.md")
    if mcp_md.exists():
        write(
            "mcp.html",
            title="MCP server",
            eyebrow="Agents",
            body=f'<div class="prose">{render_md(mcp_md.read_text(), "")}</div>',
            desc="Connect an AI agent to the Payout API over MCP.",
        )
        search.append(
            {"kind": "agents", "title": "MCP server", "ctx": "Connect Claude, Cursor, Codex", "url": "mcp.html"}
        )

    # --- landing -----------------------------------------------------------
    cards = "".join(
        f"<li><a href='api/{s}.html'><strong>{html.escape((sp.get('info') or {}).get('title', s))}</strong></a> — "
        f"{sum(len(v) for v in (sp.get('paths') or {}).values())} endpoints</li>"
        for s, sp in specs.items()
    )
    landing = (
        '<div class="prose">'
        "<p>REST APIs for payments, open banking and identity — plus an MCP server so agents "
        "can read the same reference and call the sandbox directly.</p>"
        f"<h2>API reference</h2><ul>{cards}</ul>"
        "<h2>Agents</h2><p><a href='mcp.html'>MCP server</a> — connect Claude Code, Cursor, "
        "VS Code or Codex to the Payout API.</p>"
        f"<h2>Guides</h2><p>{len(seen)} integration guides, listed in the sidebar.</p>"
        "</div>"
    )
    write("index.html", title="Payout Developers", eyebrow="Documentation", body=landing,
          desc="Payout developer documentation.")

    (out / "search-index.json").write_text(json.dumps(search, separators=(",", ":")))

    print(f"  {len(specs)} API references")
    print(f"  {len(seen)} guides")
    print(f"  {len(search)} search entries")
    print(f"  -> {out}/")


if __name__ == "__main__":
    main()

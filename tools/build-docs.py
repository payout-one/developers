#!/usr/bin/env python3
"""
Build a static API reference page from an exported Postman collection.

Faithful port: every description, table and code sample is carried over
verbatim from the collection. No rewriting, no summarising -- so the new
page can be diffed against the current Postman-hosted docs.

  venv/bin/python build-docs.py <collection.json> <out.html> [--title "..."]
"""

import html
import json
import re
import sys
from pathlib import Path

import markdown

MD = markdown.Markdown(
    extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
    output_format="html",
)


def desc(x):
    """Postman stores descriptions as either a string or {content, type}."""
    if isinstance(x, dict):
        return x.get("content") or ""
    return x or ""


def postprocess(h):
    """Adapt rendered markdown to the page shell."""
    # Wide tables need their own scroll container, or the body scrolls sideways.
    h = re.sub(r"<table>", '<div class="table-scroll"><table>', h)
    h = re.sub(r"</table>", "</table></div>", h)
    # The artifact CSP blocks external hosts, so statics.payout.one images
    # cannot load here. Surface them as links rather than broken icons.
    def img(m):
        src = m.group(1)
        return (
            f'<a class="missing-img" href="{src}" target="_blank" rel="noopener">'
            f"diagram → {html.escape(src.rsplit('/', 1)[-1])}</a>"
        )
    h = re.sub(r'<img[^>]*src="([^"]+)"[^>]*/?>', img, h)
    return h


def md(text):
    if not text.strip():
        return ""
    MD.reset()
    return postprocess(MD.convert(text))


def slug(s, seen={}):
    b = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "section"
    seen[b] = seen.get(b, 0) + 1
    return b if seen[b] == 1 else f"{b}-{seen[b]}"


def raw_url(r):
    u = r.get("url")
    if isinstance(u, dict):
        return u.get("raw", "")
    return u or ""


def pretty_path(url):
    """Strip the {{protocol}}://{{host}} prefix; keep the path readable."""
    p = re.sub(r"^\{\{[^}]+\}\}://\{\{[^}]+\}\}", "", url)
    p = re.sub(r"^https?://\{\{[^}]+\}\}", "", p)
    return p or url


def collect(items, out, depth=0):
    for it in items or []:
        if "item" in it:
            out.append(("folder", it.get("name", ""), desc(it.get("description")), None))
            collect(it["item"], out, depth + 1)
        else:
            out.append(("request", it.get("name", ""), desc((it.get("request") or {}).get("description")), it))


def build(coll, title):
    info = coll.get("info") or {}
    nodes = []
    collect(coll.get("item"), nodes)

    nav, body = [], []
    nav_open = False  # whether a <ul> is currently open

    for kind, name, d, it in nodes:
        if kind == "folder":
            sid = slug(name)
            if nav_open:
                nav.append("</ul>")
            nav.append(f'<h2><a href="#{sid}">{html.escape(name)}</a></h2><ul>')
            nav_open = True
            body.append(
                f'<section class="group" id="{sid}">'
                f"<h2>{html.escape(name)}</h2>"
                f'<div class="prose">{md(d)}</div>'
            )
        else:
            r = it.get("request") or {}
            method = (r.get("method") or "GET").upper()
            path = pretty_path(raw_url(r))
            sid = slug(name)
            if not nav_open:  # request sitting outside any folder
                nav.append('<h2>Other</h2><ul>')
                nav_open = True
            nav.append(
                f'<li><a href="#{sid}"><span class="verb {method.lower()}">{method}</span>'
                f"{html.escape(name.strip())}</a></li>"
            )

            b = r.get("body") or {}
            sample = b.get("raw") or "" if b.get("mode") == "raw" else ""
            headers = [
                h for h in (r.get("header") or [])
                if not h.get("disabled") and h.get("key")
            ]

            example = ""
            if headers:
                hlines = "\n".join(
                    f"{html.escape(h['key'])}: {html.escape(str(h.get('value','')))}"
                    for h in headers
                )
                example += f"<h4>Headers</h4><pre><code>{hlines}</code></pre>"
            if sample:
                example += f"<h4>Request body</h4><pre><code>{html.escape(sample)}</code></pre>"
            if not example:
                example = (
                    f"<h4>Request</h4><pre><code>{method} {html.escape(path)}</code></pre>"
                )

            # Reference tables need the full column width -- squeezed into the
            # half-width doc column their description cell wraps to one word
            # per line. Those endpoints stack the example underneath instead.
            doc_html = md(d)
            wide = " wide" if "<table>" in doc_html else ""

            body.append(
                f'<article class="endpoint{wide}" id="{sid}">'
                f'<div class="endpoint-doc">'
                f"<h3>{html.escape(name.strip())}</h3>"
                f'<div class="sig"><span class="verb {method.lower()}">{method}</span>'
                f'<span class="path">{html.escape(path)}</span></div>'
                f'<div class="prose">{doc_html}</div>'
                f"</div>"
                f'<div class="example">{example}</div>'
                f"</article>"
            )

    navhtml = "".join(nav) + ("</ul>" if nav_open else "")

    # Each folder opens a <section>; close the previous one before the next.
    bodyhtml = ""
    open_section = False
    for chunk in body:
        if chunk.startswith("<section"):
            if open_section:
                bodyhtml += "</section>"
            open_section = True
        bodyhtml += chunk
    if open_section:
        bodyhtml += "</section>"

    intro = md(desc(info.get("description")))

    tpl = Path(__file__).with_name("docs-shell.html").read_text()
    return (
        tpl.replace("{{TITLE}}", html.escape(title))
        .replace("{{INTRO}}", intro)
        .replace("{{NAV}}", navhtml)
        .replace("{{BODY}}", bodyhtml)
    )


PREVIEW_BANNER = (
    '<div class="banner">\n'
    "  <strong>PREVIEW</strong>\n"
    "  <span>Faithful port of the current Postman docs — every description carried over "
    "verbatim. Fixes and additions come next.</span>\n"
    "</div>"
)

DOC_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{desc}">
"""


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    title = "Payment API"
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    standalone = "--standalone" in sys.argv

    coll = json.loads(Path(src).read_text())
    page = build(coll, title)

    if standalone:
        # Served as a real file (GitHub Pages / nginx), not wrapped by a host.
        page = page.replace(PREVIEW_BANNER, "")
        page = (
            DOC_HEAD.format(desc=html.escape(f"{title} reference — Payout"))
            + page
            + "\n</body>\n</html>\n"
        )
        page = page.replace("<title>", "<title>", 1)
        # move </head> in after the <style> block
        page = page.replace("</style>\n", "</style>\n</head>\n<body>\n", 1)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(page)
    print(f"wrote {out} ({Path(out).stat().st_size // 1024} KB)")

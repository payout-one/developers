# API reference generator

Builds the self-hosted API references under `docs/api/` from API collections.
Replaces the Postman-hosted documentation at `postman.payout.one`,
`postman-intel.payout.one` and the `documenter.getpostman.com` links.

```bash
make docs     # rebuild every reference
make serve    # preview the whole site locally
make clean    # remove docs/api/
```

The first run creates `tools/.venv` and installs `markdown` into it. Your global
Python environment is not touched.

## Where the source comes from

`COLLECTIONS` points at a directory of Postman collection JSON files, defaulting
to `~/postman-export/collections`:

```bash
make docs COLLECTIONS=/path/to/collections
```

This is deliberately temporary. Postman collections are the source today because
that is where the documentation currently lives. The target is for each service to
generate its own OpenAPI spec from its router — at which point `COLLECTIONS` is
replaced by spec paths and `build-docs.py` reads those instead. The page template
and layout do not change.

## Files

| File | Role |
| --- | --- |
| `build-docs.py` | Collection JSON → HTML. Renders descriptions with `markdown` (tables, fenced code, sane lists). |
| `docs-shell.html` | Page template and all styling. Placeholders: `{{TITLE}}`, `{{INTRO}}`, `{{NAV}}`, `{{BODY}}`. |
| `requirements.txt` | Python dependencies for the venv. |

Direct invocation, if you need a one-off:

```bash
tools/.venv/bin/python tools/build-docs.py \
  ~/postman-export/collections/Payout_IE_API.json \
  docs/api/payment/index.html \
  --title "Payment API" --standalone
```

`--standalone` emits a complete HTML document for serving as a real file. Without
it the output is a fragment, suitable for embedding in a host that supplies its own
`<head>`.

## Design notes

- **Verbatim port.** Descriptions, tables and samples are carried over from the
  collections unchanged, so the generated pages can be diffed against the live
  Postman docs before Postman is switched off. Content changes belong in a
  separate pass, after the port is confirmed correct.
- **Real files, not docsify routes.** docsify uses hash routing, so `docs/api/*`
  is served directly by GitHub Pages and never touches the SPA router.
- **Theming.** The template supports light and dark via `prefers-color-scheme`
  plus `data-theme` overrides. It is independent of the docsify theme.
- **External images.** Diagrams on `statics.payout.one` render as links when a
  host blocks external assets; they load normally from our own hosting.

## Known gaps

- **PayoutID Verifications** has no page. Its endpoints are spread across the
  OAuth2 and PayoutID collections and need merging into one reference first.
- **Coverage.** The Payment API page documents 11 endpoints; `payout_api` serves
  considerably more. Generating from an application-produced OpenAPI spec closes
  this — and prevents the drift that left the old `postman/` collections repo
  stale from 2020 onward.

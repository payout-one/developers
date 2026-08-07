# Payout developer documentation.
#
#   make            spec + docs
#   make spec       Postman collections -> OpenAPI 3.1 (docs/openapi/*.yaml)
#   make docs       OpenAPI -> Scalar reference pages (docs/api/*/index.html)
#   make validate   check every spec against the OpenAPI 3.1 schema
#   make serve      preview the site locally
#   make vendor     re-download the pinned Scalar bundle
#   make clean      remove generated pages and specs
#
# The OpenAPI spec is the single source of truth: it feeds the Scalar docs, the
# MCP server, and Bruno collections. Collections are the input today only
# because that is where the documentation currently lives -- once payout_api
# generates a spec from its router via open_api_spex, point SPEC_SRC at that
# and drop the conversion step.

COLLECTIONS ?= $(HOME)/postman-export/collections
VENV        := tools/.venv
PY          := $(VENV)/bin/python
SPECS       := docs/openapi
SCALAR_URL  := https://cdn.jsdelivr.net/npm/@scalar/api-reference

.PHONY: all spec docs validate serve vendor clean venv _spec1 _page1

all: spec docs

$(VENV):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet --upgrade pip
	$(VENV)/bin/pip install --quiet -r tools/requirements.txt

venv: $(VENV)

# --- collections -> OpenAPI ------------------------------------------------
spec: $(VENV)
	@if [ ! -d "$(COLLECTIONS)" ]; then \
		echo "error: COLLECTIONS not found: $(COLLECTIONS)"; exit 1; fi
	@mkdir -p $(SPECS)
	@$(MAKE) --no-print-directory _spec1 SLUG=payment   SRC=Payout_IE_API                TITLE="Payout Payment API"
	@$(MAKE) --no-print-directory _spec1 SLUG=intel     SRC=Payout_Intel_API             TITLE="Payout Intel API"
	@$(MAKE) --no-print-directory _spec1 SLUG=psd2      SRC=PSD2-v1.0                    TITLE="Payout OpenBanking PSD2 API"
	@$(MAKE) --no-print-directory _spec1 SLUG=banklink  SRC=Banklink                     TITLE="Payout Banklink API"
	@$(MAKE) --no-print-directory _spec1 SLUG=payout-id SRC=Payout_OAuth2_New_Production TITLE="PayoutID OAuth2"

_spec1:
	@src="$(COLLECTIONS)/$(SRC).json"; \
	if [ ! -f "$$src" ]; then echo "skip $(SLUG) — missing $(SRC).json"; exit 0; fi; \
	$(PY) tools/collection-to-openapi.py "$$src" "$(SPECS)/$(SLUG).yaml" --title "$(TITLE)"

# --- OpenAPI -> Scalar pages ----------------------------------------------
docs: $(VENV) docs/vendor/scalar.js
	@$(MAKE) --no-print-directory _page1 SLUG=payment   TITLE="Payment API"
	@$(MAKE) --no-print-directory _page1 SLUG=intel     TITLE="Intel API"
	@$(MAKE) --no-print-directory _page1 SLUG=psd2      TITLE="OpenBanking PSD2 API"
	@$(MAKE) --no-print-directory _page1 SLUG=banklink  TITLE="Banklink API"
	@$(MAKE) --no-print-directory _page1 SLUG=payout-id TITLE="PayoutID OAuth2"

_page1:
	@if [ ! -f "$(SPECS)/$(SLUG).yaml" ]; then echo "skip $(SLUG) — no spec"; exit 0; fi; \
	mkdir -p docs/api/$(SLUG); \
	sed -e 's|{{TITLE}}|$(TITLE)|g' \
	    -e 's|{{SPEC}}|/openapi/$(SLUG).yaml|g' \
	    -e 's|{{VENDOR}}|/vendor/scalar.js|g' \
	    tools/scalar-page.html > docs/api/$(SLUG)/index.html; \
	echo "wrote docs/api/$(SLUG)/index.html"

validate: $(VENV)
	@$(PY) -c "import glob,yaml,sys; \
from openapi_spec_validator import validate; \
bad=0; \
[ (lambda f: [ (lambda s: [validate(s), print('  VALID  ',f)])(yaml.safe_load(open(f))) ])(f) for f in sorted(glob.glob('$(SPECS)/*.yaml')) ]; \
sys.exit(bad)"

docs/vendor/scalar.js:
	@mkdir -p docs/vendor
	curl -sSL --fail -o docs/vendor/scalar.js "$(SCALAR_URL)"
	@echo "vendored $$(du -h docs/vendor/scalar.js | cut -f1) scalar bundle"

vendor:
	@rm -f docs/vendor/scalar.js
	@$(MAKE) --no-print-directory docs/vendor/scalar.js

serve:
	npx docsify-cli serve docs

clean:
	rm -rf docs/api $(SPECS)

# --- unified preview site (docs/next) --------------------------------------
# Renders guides + OpenAPI references in one design. Built alongside the live
# docsify site, not over it -- evaluate before deciding to cut over.
site: $(VENV) spec
	@$(PY) tools/build-site.py --docs docs --out docs/next

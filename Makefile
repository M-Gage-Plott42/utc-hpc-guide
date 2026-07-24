SHELL := /bin/bash

.PHONY: help setup lint scrub test-scrub check-assets check-links check

ASSET_CHECK_SCRIPT := scripts/check_assets.py
MARKDOWNLINT := ./node_modules/.bin/markdownlint
SCRUB_CHECK_SCRIPT := scripts/check_public_scrub.py
SCRUB_POLICY := scripts/public_scrub_exceptions.json

help:
	@echo "Available targets:"
	@echo "  make setup       - Install the locked local Node quality toolchain"
	@echo "  make lint        - Run markdown lint checks"
	@echo "  make scrub       - Scan every tracked text file against public scrub policy"
	@echo "  make test-scrub  - Run scrub-checker failure-path tests"
	@echo "  make check-assets - Enforce sanitized asset naming and empty metadata"
	@echo "  make check-links - Validate local Markdown links"
	@echo "  make check       - Run lint + scrub + asset + link checks"

setup:
	npm ci

lint:
	@test -x "$(MARKDOWNLINT)" || { echo "Local markdownlint not found; run 'npm ci' first."; exit 1; }
	@git ls-files -z -- '*.md' | xargs -0 "$(MARKDOWNLINT)" --config .markdownlint.yaml

scrub:
	@python3 $(SCRUB_CHECK_SCRIPT) --policy $(SCRUB_POLICY)

test-scrub:
	@python3 -m unittest tests.test_check_public_scrub

check-assets:
	@python3 $(ASSET_CHECK_SCRIPT)

check-links:
	@set -euo pipefail; \
	missing=0; \
	while IFS= read -r file; do \
	  dir=$$(dirname "$$file"); \
	  while IFS= read -r match; do \
	    link=$$(printf '%s' "$$match" | sed -E 's/.*\(([^)]+)\).*/\1/'); \
	    if [[ "$$link" == http://* || "$$link" == https://* || "$$link" == mailto:* || "$$link" == \#* ]]; then \
	      continue; \
	    fi; \
	    target_no_anchor=$${link%%#*}; \
	    if [ -z "$$target_no_anchor" ]; then \
	      continue; \
	    fi; \
	    if [ "$${target_no_anchor#/}" != "$$target_no_anchor" ]; then \
	      path=".$$target_no_anchor"; \
	    else \
	      path="$$dir/$$target_no_anchor"; \
	    fi; \
	    if [ ! -e "$$path" ]; then \
	      echo "MISSING: $$file -> $$link (resolved: $$path)"; \
	      missing=1; \
	    fi; \
	  done < <(rg -n -o '\[[^]]+\]\([^)]+\)' "$$file"); \
	done < <(rg --files -g '*.md'); \
	if [ $$missing -eq 0 ]; then \
	  echo "all_local_markdown_links_resolve"; \
	else \
	  exit 1; \
	fi

check: lint scrub test-scrub check-assets check-links

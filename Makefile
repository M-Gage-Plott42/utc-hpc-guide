SHELL := /bin/bash

.PHONY: help lint scrub check-assets check-links check

SCRUB_PATHS := README.md docs examples assets/ood/README.md
ASSET_CHECK_SCRIPT := scripts/check_assets.py

help:
	@echo "Available targets:"
	@echo "  make lint        - Run markdown lint checks"
	@echo "  make scrub       - Run strict-fail + manual-review public scrub scans"
	@echo "  make check-assets - Enforce sanitized asset naming and empty metadata"
	@echo "  make check-links - Validate local Markdown links"
	@echo "  make check       - Run lint + scrub + asset + link checks"

lint:
	@command -v markdownlint >/dev/null || { echo "markdownlint not found; install it first."; exit 1; }
	markdownlint "**/*.md" --config .markdownlint.yaml

scrub:
	@set -euo pipefail; \
	echo "Scan 1/2 (strict fail): leaked internal markers and sensitive literals"; \
	if rg -n --no-heading "simcenter|research\\.utc\\.edu|epyc[0-9]+|abc123|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]+PRIVATE KEY-----|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|/home/[A-Za-z0-9._-]+" $(SCRUB_PATHS); then \
	  echo "ERROR: strict scrub scan matched one or more forbidden patterns."; \
	  exit 1; \
	fi; \
	echo "strict_scrub_clean"; \
	echo "Scan 2/2 (manual review): contextual terms to verify before release"; \
	rg -n --no-heading "@|/home/|login|partition|account|allocation|project|token|secret" $(SCRUB_PATHS) || true

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

check: lint scrub check-assets check-links

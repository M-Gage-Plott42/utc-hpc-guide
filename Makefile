SHELL := /bin/bash

.PHONY: help lint scrub check-links check

SCRUB_PATHS := README.md docs examples assets/ood/README.md

help:
	@echo "Available targets:"
	@echo "  make lint        - Run markdown lint checks"
	@echo "  make scrub       - Run high-signal public scrub scans"
	@echo "  make check-links - Validate local Markdown links"
	@echo "  make check       - Run lint + scrub + link checks"

lint:
	@command -v markdownlint >/dev/null || { echo "markdownlint not found; install it first."; exit 1; }
	markdownlint "**/*.md" --config .markdownlint.yaml

scrub:
	@echo "Scan 1/2: likely leaked internal cluster markers"
	rg -n "simcenter|research\\.utc\\.edu|epyc[0-9]+|abc123" $(SCRUB_PATHS) || true
	@echo "Scan 2/2: likely sensitive literals (keys, emails, concrete home paths)"
	rg -n "(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]+PRIVATE KEY-----|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|/home/[A-Za-z0-9._-]+)" $(SCRUB_PATHS) || true

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

check: lint scrub check-links

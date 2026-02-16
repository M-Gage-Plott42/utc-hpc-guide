SHELL := /bin/bash

.PHONY: lint scrub check-links check

lint:
	@command -v markdownlint >/dev/null || { echo "markdownlint not found; install it first."; exit 1; }
	markdownlint "**/*.md" --config .markdownlint.yaml

scrub:
	rg -n "@|/home/|login|partition|account|allocation|project|token|secret" . || true
	rg -n "utc|simcenter|research\\.utc\\.edu|epyc|abc123|Gage Plott" docs examples README.md || true

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

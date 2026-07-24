SHELL := /bin/bash

.PHONY: help setup lint scrub test-scrub check-assets check-links test-links check

ASSET_CHECK_SCRIPT := scripts/check_assets.py
MARKDOWNLINT := ./node_modules/.bin/markdownlint
SCRUB_CHECK_SCRIPT := scripts/check_public_scrub.py
SCRUB_POLICY := scripts/public_scrub_exceptions.json
LINK_CHECK_SCRIPT := scripts/check_links.py

help:
	@echo "Available targets:"
	@echo "  make setup       - Install the locked local Node quality toolchain"
	@echo "  make lint        - Run markdown lint checks"
	@echo "  make scrub       - Scan every tracked text file against public scrub policy"
	@echo "  make test-scrub  - Run scrub-checker failure-path tests"
	@echo "  make check-assets - Enforce sanitized asset naming and empty metadata"
	@echo "  make check-links - Parse and validate local links, references, and anchors"
	@echo "  make test-links  - Run link-parser failure-path tests"
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
	@python3 $(LINK_CHECK_SCRIPT)

test-links:
	@python3 -m unittest tests.test_check_links

check: lint scrub test-scrub check-assets check-links test-links

SHELL := /bin/bash

.PHONY: help setup lint scrub test-scrub check-assets test-assets check-links test-links check-placeholders test-placeholders pdf check-pdf check

ASSET_CHECK_SCRIPT := scripts/check_assets.py
MARKDOWNLINT := ./node_modules/.bin/markdownlint
SCRUB_CHECK_SCRIPT := scripts/check_public_scrub.py
SCRUB_POLICY := scripts/public_scrub_exceptions.json
LINK_CHECK_SCRIPT := scripts/check_links.py
PLACEHOLDER_CHECK_SCRIPT := scripts/check_shell_placeholders.py
PDF_BUILD_SCRIPT := scripts/build_pdf.py
PDF_CHECK_SCRIPT := scripts/check_pdf.py
PDF_MANIFEST := pdf/guide_manifest.json
PDF_OUTPUT := dist/UTC_HPC_Guide.pdf

help:
	@echo "Available targets:"
	@echo "  make setup       - Install the locked local Node quality toolchain"
	@echo "  make lint        - Run markdown lint checks"
	@echo "  make scrub       - Scan every tracked text file against public scrub policy"
	@echo "  make test-scrub  - Run scrub-checker failure-path tests"
	@echo "  make check-assets - Enforce PNG structure, decode, and privacy policy"
	@echo "  make test-assets - Run PNG validation failure-path tests"
	@echo "  make check-links - Parse and validate local links, references, and anchors"
	@echo "  make test-links  - Run link-parser failure-path tests"
	@echo "  make check-placeholders - Reject unsafe angle placeholders in shell examples"
	@echo "  make test-placeholders - Run shell-placeholder failure-path tests"
	@echo "  make pdf         - Build the printable release PDF"
	@echo "  make check-pdf   - Rebuild twice, compare bytes, and run PDF QA"
	@echo "  make check       - Run lint + scrub + asset + link + placeholder checks"

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

test-assets:
	@python3 -m unittest tests.test_check_assets

check-links:
	@python3 $(LINK_CHECK_SCRIPT)

test-links:
	@python3 -m unittest tests.test_check_links

check-placeholders:
	@python3 $(PLACEHOLDER_CHECK_SCRIPT)

test-placeholders:
	@python3 -m unittest tests.test_check_shell_placeholders

pdf:
	@python3 $(PDF_BUILD_SCRIPT) --manifest $(PDF_MANIFEST) --output $(PDF_OUTPUT)

check-pdf:
	@python3 $(PDF_BUILD_SCRIPT) --manifest $(PDF_MANIFEST) --output $(PDF_OUTPUT) --verify-reproducible
	@python3 $(PDF_CHECK_SCRIPT) --manifest $(PDF_MANIFEST) --pdf $(PDF_OUTPUT)

check: lint scrub test-scrub check-assets test-assets check-links test-links check-placeholders test-placeholders

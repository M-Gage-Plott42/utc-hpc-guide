SHELL := /bin/bash

.PHONY: help setup setup-pdf-tools lint scrub test-scrub check-assets test-assets check-links test-links test-external-links check-external-links check-placeholders test-placeholders test-build-pdf test-pdf-ocr test-pdf-accessibility test-pdf-toolchain-bootstrap test-pdf-toolchain-record check-shell-syntax check-shell-lint check-whitespace pdf check-pdf-ocr check-pdf-accessibility check-pdf check release-check

ASSET_CHECK_SCRIPT := scripts/check_assets.py
MARKDOWNLINT := ./node_modules/.bin/markdownlint
SCRUB_CHECK_SCRIPT := scripts/check_public_scrub.py
SCRUB_POLICY := scripts/public_scrub_exceptions.json
LINK_CHECK_SCRIPT := scripts/check_links.py
EXTERNAL_LINK_CHECK_SCRIPT := scripts/check_external_links.py
EXTERNAL_LINK_POLICY := scripts/external_link_policy.json
PLACEHOLDER_CHECK_SCRIPT := scripts/check_shell_placeholders.py
PDF_BUILD_SCRIPT := scripts/build_pdf.py
PDF_CHECK_SCRIPT := scripts/check_pdf.py
PDF_OCR_CHECK_SCRIPT := scripts/check_pdf_ocr.py
PDF_ACCESSIBILITY_CHECK_SCRIPT := scripts/check_pdf_accessibility.py
PDF_TOOLCHAIN_BOOTSTRAP := scripts/bootstrap_pdf_toolchain.py
PDF_TOOLCHAIN_LOCK := pdf/toolchain.lock.json
PDF_TOOLCHAIN_ROOT ?= .cache/pdf-toolchain
PDF_TOOLCHAIN_BIN := $(abspath $(PDF_TOOLCHAIN_ROOT))/bin
PDF_MANIFEST := pdf/guide_manifest.json

help:
	@echo "Available targets:"
	@echo "  make setup       - Install the locked local Node quality toolchain"
	@echo "  make setup-pdf-tools - Verify and install the locked tagged-PDF toolchain"
	@echo "  make lint        - Run markdown lint checks"
	@echo "  make scrub       - Scan every tracked text file against public scrub policy"
	@echo "  make test-scrub  - Run scrub-checker failure-path tests"
	@echo "  make check-assets - Enforce asset paths plus PNG structure/metadata policy"
	@echo "  make test-assets - Run PNG validation failure-path tests"
	@echo "  make check-links - Parse and validate local links, references, and anchors"
	@echo "  make test-links  - Run link-parser failure-path tests"
	@echo "  make test-external-links - Run external-link monitor unit tests"
	@echo "  make check-external-links - Run the separate network link monitor"
	@echo "  make check-placeholders - Reject unsafe angle placeholders in shell examples"
	@echo "  make test-placeholders - Run shell-placeholder failure-path tests"
	@echo "  make test-build-pdf - Run PDF manifest/build failure-path tests"
	@echo "  make test-pdf-ocr - Run PDF OCR checker failure-path tests"
	@echo "  make test-pdf-accessibility - Run PDF accessibility failure-path tests"
	@echo "  make test-pdf-toolchain-bootstrap - Run locked-bootstrap failure-path tests"
	@echo "  make test-pdf-toolchain-record - Run PDF build-record failure-path tests"
	@echo "  make check-shell-syntax - Run bash syntax checks on tracked sbatch examples"
	@echo "  make check-shell-lint - Run ShellCheck on tracked sbatch examples"
	@echo "  make check-whitespace - Check staged/unstaged lines for whitespace errors"
	@echo "  make pdf         - Build the printable release-candidate PDF"
	@echo "  make check-pdf-ocr - OCR every page of the existing candidate PDF"
	@echo "  make check-pdf-accessibility - Run structural and veraPDF PDF/UA-2 QA"
	@echo "  make check-pdf   - Rebuild twice and run structural/PDF-UA/OCR QA"
	@echo "  make check       - Run lint + scrub + asset + link + placeholder checks"
	@echo "  make release-check - Run the complete local release gate"

setup:
	npm ci

setup-pdf-tools:
	@python3 $(PDF_TOOLCHAIN_BOOTSTRAP) --lock $(PDF_TOOLCHAIN_LOCK) --root $(PDF_TOOLCHAIN_ROOT)

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

test-external-links:
	@python3 -m unittest tests.test_check_external_links

check-external-links:
	@python3 $(EXTERNAL_LINK_CHECK_SCRIPT) --policy $(EXTERNAL_LINK_POLICY)

check-placeholders:
	@python3 $(PLACEHOLDER_CHECK_SCRIPT)

test-placeholders:
	@python3 -m unittest tests.test_check_shell_placeholders

test-build-pdf:
	@python3 -m unittest tests.test_build_pdf

test-pdf-ocr:
	@python3 -m unittest tests.test_check_pdf_ocr

test-pdf-accessibility:
	@python3 -m unittest tests.test_check_pdf_accessibility

test-pdf-toolchain-bootstrap:
	@python3 -m unittest tests.test_bootstrap_pdf_toolchain

test-pdf-toolchain-record:
	@python3 -m unittest tests.test_write_pdf_toolchain_record

check-shell-syntax:
	@mapfile -d '' shell_files < <(git ls-files -z -- 'examples/*.sbatch'); \
	if (( $${#shell_files[@]} == 0 )); then \
		echo "No tracked sbatch examples found."; \
		exit 0; \
	fi; \
	for shell_file in "$${shell_files[@]}"; do \
		bash -n -- "$$shell_file"; \
	done; \
	echo "shell_syntax_clean files=$${#shell_files[@]}"

check-shell-lint:
	@command -v shellcheck >/dev/null 2>&1 || { \
		echo "ShellCheck not found; install it (for example, 'sudo apt-get install shellcheck') and retry." >&2; \
		exit 1; \
	}
	@mapfile -d '' shell_files < <(git ls-files -z -- 'examples/*.sbatch'); \
	if (( $${#shell_files[@]} == 0 )); then \
		echo "No tracked sbatch examples found."; \
		exit 0; \
	fi; \
	for shell_file in "$${shell_files[@]}"; do \
		shellcheck -s bash -- "$$shell_file"; \
	done; \
	echo "shell_lint_clean files=$${#shell_files[@]}"

check-whitespace:
	@git diff --check
	@git diff --cached --check

pdf: setup-pdf-tools
	@PATH="$(PDF_TOOLCHAIN_BIN):$$PATH" python3 $(PDF_BUILD_SCRIPT) --manifest $(PDF_MANIFEST)

check-pdf-ocr: setup-pdf-tools
	@PATH="$(PDF_TOOLCHAIN_BIN):$$PATH" python3 $(PDF_OCR_CHECK_SCRIPT) --manifest $(PDF_MANIFEST)

check-pdf-accessibility: setup-pdf-tools
	@PATH="$(PDF_TOOLCHAIN_BIN):$$PATH" python3 $(PDF_ACCESSIBILITY_CHECK_SCRIPT) --manifest $(PDF_MANIFEST) --verapdf "$(PDF_TOOLCHAIN_BIN)/verapdf" --report dist/verapdf-report.xml

check-pdf: setup-pdf-tools
	@PATH="$(PDF_TOOLCHAIN_BIN):$$PATH" python3 $(PDF_BUILD_SCRIPT) --manifest $(PDF_MANIFEST) --verify-reproducible
	@PATH="$(PDF_TOOLCHAIN_BIN):$$PATH" python3 $(PDF_CHECK_SCRIPT) --manifest $(PDF_MANIFEST)
	@PATH="$(PDF_TOOLCHAIN_BIN):$$PATH" python3 $(PDF_OCR_CHECK_SCRIPT) --manifest $(PDF_MANIFEST)
	@PATH="$(PDF_TOOLCHAIN_BIN):$$PATH" python3 $(PDF_ACCESSIBILITY_CHECK_SCRIPT) --manifest $(PDF_MANIFEST) --verapdf "$(PDF_TOOLCHAIN_BIN)/verapdf" --report dist/verapdf-report.xml

check: lint scrub test-scrub check-assets test-assets check-links test-links test-external-links check-placeholders test-placeholders test-build-pdf test-pdf-ocr test-pdf-accessibility test-pdf-toolchain-bootstrap test-pdf-toolchain-record

release-check: check check-shell-syntax check-shell-lint check-pdf check-whitespace

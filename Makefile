.PHONY: install test lint canon-validate canon-hash migrate clean

# Install project in editable mode with all dependencies
install:
	pip install -e ".[dev]" 2>/dev/null || pip install -e .

# Run all tests
test:
	PYTHONPATH=$(shell pwd) pytest src/tests/ -v

# Run linter
lint:
	ruff check src/ schemas/ || true
	ruff format --check src/ schemas/ || true

# Validate canonical YAML files — exits non-zero on any failure
canon-validate:
	@echo "==> Validating canonical files..."
	PYTHONPATH=$(shell pwd) woodward canon validate; \
	STATUS=$$?; \
	if [ $$STATUS -ne 0 ]; then \
		echo "CANON VALIDATION FAILED — build stopped"; \
		exit 1; \
	fi; \
	echo "==> Canon validation PASSED"

# Emit canon hash to stdout and runs/latest/canon_hash.json
canon-hash:
	@echo "==> Emitting canon hash..."
	PYTHONPATH=$(shell pwd) woodward canon hash

# Run all DB migrations
migrate:
	@echo "==> Running DB migrations..."
	PYTHONPATH=$(shell pwd) woodward db migrate

# Show DB table counts
db-status:
	PYTHONPATH=$(shell pwd) woodward db status

# Clean generated artifacts (does NOT delete canonical files or db/)
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "==> Clean complete"

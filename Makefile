.PHONY: audit audit-strict format lint

audit:
	pip-audit -r requirements.txt || true
	safety check -r requirements.txt || true

audit-strict:
	pip-audit -r requirements.txt --strict

format:
	black .
	ruff check . --fix

lint:
	ruff check .
	black --check .

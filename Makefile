.PHONY: audit audit-strict

audit:
	pip-audit -r requirements.txt || true
	safety check -r requirements.txt || true

audit-strict:
	pip-audit -r requirements.txt --strict

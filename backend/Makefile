.PHONY: venv install dev

venv:
	python3 -m venv .venv

install: venv
	.venv/bin/pip install -r requirements.txt

dev:
	DATA_DIR=./data .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

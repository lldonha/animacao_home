.PHONY: setup run test lint clean

VENV?=.venv
PYTHON?=python3
PIP?=$(VENV)/bin/pip
UVICORN?=$(VENV)/bin/uvicorn
PYTEST?=$(VENV)/bin/pytest

setup:
$(PYTHON) -m venv $(VENV)
$(PIP) install --upgrade pip
$(PIP) install -r requirements.txt

run:
$(UVICORN) app.main:app --host 0.0.0.0 --port 8000

test:
$(PYTEST) -q

lint:
$(VENV)/bin/ruff check .

clean:
rm -rf $(VENV) assets/frames/* assets/outputs/* final_renders/*

PY = python3
VENV = venv
BIN = $(VENV)/bin
DATA_FOLDER = data
# make it work on windows too
ifeq ($(OS), Windows_NT)
    BIN=$(VENV)/Scripts
    PY=python
endif

install: $(VENV)

install-dev: install $(DATA_FOLDER) $(VENV)/devel requirements-dev.txt
	$(BIN)/pip install --upgrade -r requirements-dev.txt
	touch $(VENV)/devel

$(DATA_FOLDER):
	mkdir $(DATA_FOLDER)

$(VENV): requirements.txt
	python3 -m venv venv
	$(BIN)/pip install --upgrade -r requirements.txt
	touch $(VENV)

.PHONY: format
format: $(VENV)
	$(BIN)/black emo tests
	$(BIN)/isort emo tests

.PHONY: lint
lint: $(VENV)
	$(BIN)/flake8 emo tests

.PHONY: test-only
test-only: $(VENV)
	$(BIN)/pytest

.PHONY: test
test: lint test-only

.PHONY: run-dev
run-dev: $(VENV) $(DATA_FOLDER)
	$(BIN)/uvicorn emo.main:app --reload

.PHONY: run
run: $(VENV)
	$(BIN)/uvicorn emo.main:app

clean:
	find . -type f -name .coverage -delete
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
	find . -type d -name .pytest_cache -exec rm -rv {} +
	find . -type d -name coverage_html -exec rm -rv {} +

clean-deep: clean
	rm -rf $(VENV)
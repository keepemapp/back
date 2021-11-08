PY = python3.9
VENV = venv
BIN = $(VENV)/bin
DATA_FOLDER = data
# make it work on windows too
ifeq ($(OS), Windows_NT)
    BIN=$(VENV)/Scripts
    PY=python
endif

install: $(VENV)
	#sudo apt-get install python3.8 python3.8-dev python3.8-venv python3-pip
	$(BIN)/$(PY) -m pip install --upgrade -r requirements.txt
	echo "installed"

install-dev: install $(DATA_FOLDER) requirements-dev.txt
	$(BIN)/$(PY) -m pip install --upgrade -r requirements-dev.txt

$(DATA_FOLDER):
	mkdir $(DATA_FOLDER)

$(VENV): requirements.txt
	$(PY) -m venv venv
	wget https://bootstrap.pypa.io/get-pip.py && $(BIN)/$(PY) get-pip.py && rm get-pip.py
	touch $(VENV)

.PHONY: format
format: $(VENV)
	$(BIN)/black --line-length 79 emo tests
	$(BIN)/isort emo tests

.PHONY: lint
lint: $(VENV)
	$(BIN)/flake8 emo

.PHONY: test-only
test-only: $(VENV)
	$(BIN)/pytest

.PHONY: test
test: lint test-only

.PHONY: precommit
precommit: format test clean

.PHONY: run-dev
run-dev: $(VENV) $(DATA_FOLDER)
	$(BIN)/uvicorn emo.main:app --reload --no-server-header

.PHONY: run
run: $(VENV)
	$(BIN)/uvicorn emo.main:app --no-server-header

clean:
	find . -type f -name .coverage -delete
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
	find . -type d -name .pytest_cache -exec rm -r {} +
	find . -type d -name .coverage_html -exec rm -r {} +

clean-deep: clean
	rm -rf $(VENV)

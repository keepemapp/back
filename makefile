ENVIRONMENT ?= dev

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
	mkdir $(DATA_FOLDER)/assets

$(VENV): requirements.txt
	$(PY) -m venv venv
	wget https://bootstrap.pypa.io/get-pip.py && $(BIN)/$(PY) get-pip.py && rm get-pip.py
	touch $(VENV)

.PHONY: format
format:
	$(BIN)/isort kpm tests --profile black --line-length 79
	$(BIN)/black --line-length 79 kpm tests

.PHONY: lint
lint:
	$(BIN)/flake8 kpm

.PHONY: typecheck
typecheck:
	$(BIN)/mypy kpm

.PHONY: test-only
test-only:
	source kpm/.env
	$(BIN)/pytest -n 8

.PHONY: test
test: lint test-only

.PHONY: precommit
precommit: format test clean

.PHONY: run-dev
run-dev: $(VENV) $(DATA_FOLDER)
	$(BIN)/uvicorn kpm.main:app --reload --no-server-header

run: install
	$(BIN)/uvicorn kpm.main:app --no-server-header

clean:
	find . -type f -name .coverage -delete
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
	find . -type d -name .pytest_cache -exec rm -r {} +
	find . -type d -name .coverage_html -exec rm -r {} +

clean-data:
	find $(DATA_FOLDER) -type f -delete

clean-deep: clean clean-data
	rm -rf $(VENV)


#######################
## Docker deployment ##
#######################
.PHONY: build
build:
	docker compose build

.PHONY: up
up:
	docker compose --env-file .env.$(ENVIRONMENT) up -d

.PHONY: logs
logs:
	docker compose logs --follow

.PHONY: stop
stop:
	docker compose stop

.PHONY: down
rm:
	docker compose down

.PHONY: ps
ps:
	docker compose ps
	ENVIRONMENT=qa docker compose ps
	ENVIRONMENT=prod docker compose ps

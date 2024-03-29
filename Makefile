# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29
.PHONY: app

dc = docker-compose
run = $(dc) run --rm
manage = $(run) dev python manage.py
pytest = $(run) test pytest $(ARGS)

PYTHON = python3

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements.txt requirements_dev.txt

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	## The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	## https://stackoverflow.com/questions/58843905
	pip-compile --upgrade --allow-unsafe --output-file requirements.txt requirements.in
	pip-compile --upgrade --allow-unsafe --output-file requirements_dev.txt requirements_dev.in

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:                         ## Make migrations
	$(manage) makemigrations $(ARGS)

migrate:                            ## Migrate
	$(manage) migrate

urls:                               ## Show available URLs
	$(manage) show_urls

build:                              ## Build docker image
	$(dc) build

push: build                         ## Push docker image to registry
	$(dc) push

app:                                ## Run app
	$(run) --service-ports app

bash:                               ## Run the container and start bash
	$(run) dev bash

shell:                              ## Run shell_plus and print sql
	$(manage) shell_plus --print-sql

dev: 						        ## Run the development app (and run extra migrations first)
	$(run) --service-ports dev

test: lint                               ## Execute tests
	$(dc) run --rm test pytest /app/tests $(ARGS)

parser_telcameras_v2:
	$(dc) run parser_telcameras_v2

pdb:                                ## Execute tests with python debugger
	$(dc) run --rm test pytest --pdb $(ARGS)

clean:                              ## Clean docker stuff
	$(dc) down -v --remove-orphans

env:                                ## Print current env
	env | sort

trivy: 								## Detect image vulnerabilities
	$(dc) build --no-cache app
	trivy image --ignore-unfixed docker-registry.secure.amsterdam.nl/datapunt/verkeersvergunningen

lintfix:                            ## Execute lint fixes
	$(run) test black /app/src/$(APP) /app/tests/$(APP)
	$(run) test autoflake /app --recursive --in-place --remove-unused-variables --remove-all-unused-imports --quiet
	$(run) test isort /app/src/$(APP) /app/tests/$(APP)


lint:                               ## Execute lint checks
	$(run) test autoflake /app --check --recursive --quiet
	$(run) test isort --diff --check /app/src/$(APP) /app/tests/$(APP)

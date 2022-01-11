# Development Environment

## Getting Started
This project requires the following requirements:
 - Python 3.8+
- Pipenv
- An SQL server with one database created in advance (currently only supports PostgreSQL, but could support any SQL database with minor modification through SQLAlchemy)

### Installation options
The list below shows a few different ways to get the development environment up and running.

- [Manual](../manual/README.md)
- [VSCode using devcontainers](../vscode/README.md)


## Run Test
Run unit- and integration tests:

    $ pipenv run testall

Run unit tests

    $ pipenv run unittest

Run integration tests

    $ pipenv run integrationtest

## Run linting

Run PEP8 linting:

    $ pipenv run flake8

# Updating dependencies (requirements.txt)

To add or remove Python package dependencies, first update the contents of Pipfile.

To install all dependencies from Pipfile locally (for development and testing):

    pipenv update --dev

To lock production-only dependencies (for Docker containers):

    pipenv lock -r > requirements.txt

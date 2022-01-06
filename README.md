# Auth

This is the repository for the Auth-domain - a part of [Energy Origin](https://github.com/Energinet-DataHub/energy-origin).

This domain is responsible for:

- Authenticating users via OpenID Connect
- Issuing authorization-tokens to clients
- Translating opaque tokens to internal tokens (via a Træfik ForwardAuth endpoint)


---


# Content

- Building and running the services
    - Requirements
    - Installation and running locally
    - Building and running Docker images
    - Running tests
    - Environment variables
- Architecture and implementation
- Database and migrations


---


# Introduction

TODO


## Data models

TODO


---


# System architecture

TODO


## Data models

TODO


## API endpoints

TODO


## Bus messages (in and out)

TODO


## Dependencies

TODO


---


# Configuration

The service(s) needs a number of configuration options for it to run.
Options can be defined in either of the following ways (in prioritized order):

- Environment variables
- Defined in files `settings.ini` or `.env`
- Command line arguments

For example, if an option is defined as an environment variable, it will be
used. Otherwise, the system looks towards the value in the `settings.ini` or
`env.ini` (not both), and so on.

When running the service locally for development and debugging, most of the
necessary options are defined in `settings.ini`. The remaining (secret) options
should be defined as environment variables, thus not committed to Git by accident.

## Available options

Name | Description | Example
:--- | :--- | :--- |
`DEBUG` | Whether or not to enable debugging mode (off by default) | `True`/`1` or `False`/`0`
`SERVICE_URL` | Public URL to this service without trailing slash (defaults to `https://DEVELOP_HOST:DEVELOP_PORT`) | `https://project.com/api/auth`
`DEVELOP_HOST` | Hostname used by development server (optional) | `127.0.0.1`
`DEVELOP_PORT` | Port used by development server (optional) | `9096`
**Tokens, Secrets, and Keys:** | |
`TOKEN_COOKIE_DOMAIN` | The domain to set cookie on (Bearer token) | `project.com`
`TOKEN_COOKIE_SAMESITE` | Whether the token cookie should be set as a SameSite cookie | `True`/`False`
`TOKEN_COOKIE_HTTP_ONLY` | Whether the token cookie should be set as a HttpOnly cookie | `True`/`False`
`INTERNAL_TOKEN_SECRET` | Secret to sign and verify internal tokens | `something-secret`
`SSN_ENCRYPTION_KEY` | Key en encrypt social security numbers | `also-something-secret`
**SQL:** | |
`PSQL_HOST` | PostgreSQL server hostname | `127.0.0.1`
`PSQL_PORT` | PostgreSQL server port | `5432`
`PSQL_USER` | PostgreSQL username | `postgres`
`PSQL_PASSWORD` | PostgreSQL password | `1234`
`PSQL_DB` | PostgreSQL database name | `auth`
`SQL_POOL_SIZE` | Connection pool size per container | `10`
**OpenID Connect:** | |
`OIDC_CLIENT_ID` | OpenID Connect client ID | 
`OIDC_CLIENT_SECRET` | OpenID Connect client secret | 
`OIDC_AUTHORITY_URL` | OpenID Connect authority URL | 


---


# Installation and running locally (for development)

The following sections describes how to install and run the project locally for development and debugging.


## Requirements

- Python 3.8+
- Pipenv
- An SQL server with one database created in advance (currently only supports PostgreSQL, but could support any SQL database with minor modification through SQLAlchemy)


## First time installation

Make sure to upgrade your system packages for good measure:

    $ pip install --upgrade --user setuptools pip

Install Pipenv:

    $ pip install --upgrade --user pipenv

Then install project dependencies (including dev-packages):

    $ pipenv update --dev

Define necessary options (described in a section above):

    SQL_URI=<SQL connection string>
    OIDC_CLIENT_ID=<OpenID Connect Client ID>
    OIDC_CLIENT_SECRET=<OpenID Connect Client secret>
    OIDC_AUTHORITY_URL=<OpenID Connect authority URL>

Navigate to the source directory:

    $ cd src/

Apply database migrations:

    $ pipenv run alembic --config=migrations/alembic.ini upgrade head

## Run service(s) locally (for development)

Start the local development server (NOT for production use):

    $ pipenv run python -m auth_api

## Run tests

Run unit- and integration tests:

    $ pipenv run testall

Run unit tests

    $ pipenv run unittest

Run integration tests

    $ pipenv run integrationtest

## Run linting

Run PEP8 linting:

    $ pipenv run flake8


---


# Building and running production-ready Docker image

All microservices in a domain are build into a single Docker image with multiple entrypoints.
Entrypoint scripts are located in the `src/` folder.

## Building Docker image

Start by locking dependencies (if necessary):

    pipenv lock -r > requirements.txt

Then build the Docker image:

    docker build -t auth:XX .

## Running container images

Web API:

    docker run --entrypoint /app/entrypoint_api.sh auth:XX


---

# Updating dependencies (requirements.txt)

To add or remove Python package dependencies, first update the contents of Pipfile.

To install all dependencies from Pipfile locally (for development and testing):

    pipenv update --dev

To lock production-only dependencies (for Docker containers):

    pipenv lock -r > requirements.txt


---


# SQL Database

The services make use [SQLAlchemy](https://www.sqlalchemy.org/) to connect and
interact with an SQL database. The underlying SQL server technology is of less
importance, as [SQLAlchemy supports a variety of databases](https://docs.sqlalchemy.org/en/14/core/engines.html),
even SQLite for development and debugging. One note, however, is that the
underlying driver for specific databases must be installed (via Pip/Pipfile).
Currently, only the PostgreSQL is installed.

## Connecting to database

The services require the `SQL_URI` configuration option, which must be
[in a format SQLAlchemy supports](https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls).

## Managing database migrations

The services make use of [Alembic](https://alembic.sqlalchemy.org/en/latest/)
to manage database migrations, since this feature is not build into SQLAlchemy
itself.

To create a new database revision:

    $ cd src/
    $ alembic --config=migrations/alembic.ini revision --autogenerate

To apply all existing database migrations, thus upgrading the database to the latest scheme:

    $ cd src/
    $ alembic --config=migrations/alembic.ini upgrade head

## Applying migrations in production

When starting the services through their respective entrypoints, the first thing
they do is apply migrations.

# Workflows
All workflows is described [here](.github/workflows/README.md).
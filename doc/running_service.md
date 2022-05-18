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

Creating a new database revision, requires a running database eg. postgress database.
The migration script checks the username, password, database values from the `settings.ini` file.


To create a database running postgress using docker run:
```sh
# Run postgress database with default values from settings.ini
#   Database: auth
#   password: 1234
#   username: postgres
docker run --name some-postgre s -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=auth -d postgres
```

Before creating a new revision, the local database needs to apply all existing database migrations.

To apply all existing database migrations, thus upgrading the database to the latest scheme:

    $ cd src/
    $ alembic --config=migrations/alembic.ini upgrade head


After the database has been created and made sure the database IP matches the one defined in settings.in, we can create a new database revision:

    $ cd src/
    $ alembic --config=migrations/alembic.ini revision --autogenerate



## Applying migrations in production

When starting the services through their respective entrypoints, the first thing
they do is apply migrations.

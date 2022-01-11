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
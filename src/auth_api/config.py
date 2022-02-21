import os
from datetime import timedelta
from decouple import config

# -- General -----------------------------------------------------------------

# Enable/disable debug mode
DEBUG = config('DEBUG', default=False, cast=bool)

# Service port (when running development server)
DEVELOP_HOST = config('DEVELOP_HOST', default='127.0.0.1')

# Service port (when running development server)
DEVELOP_PORT = config('DEVELOP_PORT', default=9096, cast=int)

# Service absolute URL (when running development server)
DEVELOP_URL = f'http://{DEVELOP_HOST}:{DEVELOP_PORT}'

# Service' public URL
SERVICE_URL = config('SERVICE_URL', default=DEVELOP_URL)

# Source path
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SOURCE_DIR, '..')
TERMS_MARKDOWN_PATH = os.path.join('terms', 'terms.md')

# No. of hours used for the timedelta for internal token expiry
TOKEN_EXPIRY_DELTA = timedelta(days=1)

# -- Tokens ------------------------------------------------------------------

# The domain to set token cookie on
TOKEN_COOKIE_DOMAIN = config('TOKEN_COOKIE_DOMAIN', default=DEVELOP_HOST)

# Whether the token cookie should be set as SameSite
TOKEN_COOKIE_SAMESITE = config(
    'TOKEN_COOKIE_SAMESITE', default=True, cast=bool)

# Whether the token cookie should be set as HttpOnly
TOKEN_COOKIE_HTTP_ONLY = config(
    'TOKEN_COOKIE_HTTP_ONLY', default=True, cast=bool)

# Scopes to grant when creating internal tokens
TOKEN_DEFAULT_SCOPES = [
    'meteringpoints.read',
    'measurements.read',
]


# -- Secrets -----------------------------------------------------------------

# Secret used to sign internal token
INTERNAL_TOKEN_SECRET = config('INTERNAL_TOKEN_SECRET')

# Secret used to encrypt id_token in state
STATE_ENCRYPTION_SECRET = config('STATE_ENCRYPTION_SECRET')


# -- SQL ---------------------------------------------------------------------

# PostgreSQL host
PSQL_HOST = config('PSQL_HOST')

# PostgreSQL port
PSQL_PORT = config('PSQL_PORT')

# PostgreSQL username
PSQL_USER = config('PSQL_USER')

# PostgreSQL password
PSQL_PASSWORD = config('PSQL_PASSWORD')

# PostgreSQL password
PSQL_DB = config('PSQL_DB')

# SqlAlchemy connection string
SQL_URI = f'postgresql://{PSQL_USER}:{PSQL_PASSWORD}@{PSQL_HOST}:{PSQL_PORT}/{PSQL_DB}'  # noqa: E501

# Number of concurrent connection to SQL database
SQL_POOL_SIZE = config('SQL_POOL_SIZE', default=1, cast=int)


# -- URLs --------------------------------------------------------------------

# Callback URL after OpenID Connect authentication flow
OIDC_LOGIN_CALLBACK_PATH = '/oidc/login/callback'
OIDC_LOGIN_CALLBACK_URL = \
    f'{SERVICE_URL}{OIDC_LOGIN_CALLBACK_PATH}'

# Callback URL after OpenID Connect SSN validation flow
OIDC_SSN_VALIDATE_CALLBACK_PATH = '/oidc/login/callback/ssn'
OIDC_SSN_VALIDATE_CALLBACK_URL = \
    f'{SERVICE_URL}{OIDC_SSN_VALIDATE_CALLBACK_PATH}'

# Terms Get URL
TERMS_PATH = '/terms'
TERMS_URL = \
    f'{SERVICE_URL}{TERMS_PATH}'

# Terms accept URL
TERMS_ACCEPT_PATH = '/terms/accept'
TERMS_ACCEPT_URL = \
    f'{SERVICE_URL}{TERMS_ACCEPT_PATH}'


# -- OpenID Connect ----------------------------------------------------------

OIDC_CLIENT_ID = config('OIDC_CLIENT_ID')
OIDC_CLIENT_SECRET = config('OIDC_CLIENT_SECRET')
OIDC_AUTHORITY_URL = config('OIDC_AUTHORITY_URL')
OIDC_LANGUAGE = 'en'

OIDC_LOGIN_URL = f'{OIDC_AUTHORITY_URL}/connect/authorize'
OIDC_TOKEN_URL = f'{OIDC_AUTHORITY_URL}/connect/token'
OIDC_JWKS_URL = f'{OIDC_AUTHORITY_URL}/.well-known/openid-configuration/jwks'
OIDC_API_LOGOUT_URL = f'{OIDC_AUTHORITY_URL}/api/v1/session/logout'

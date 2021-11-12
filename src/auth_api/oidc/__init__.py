from auth_api.config import (
    OIDC_CLIENT_ID,
    OIDC_CLIENT_SECRET,
    OIDC_LOGIN_URL,
    OIDC_TOKEN_URL,
    OIDC_JWKS_URL,
    OIDC_API_LOGOUT_URL,
)

from .models import OpenIDConnectToken
from .errors import OIDC_ERROR_CODES
from .session import OAuth2Session
from .signaturgruppen import SignaturgruppenBackend


# Defining the OAuth2 session as singleton here makes it easy to mock
# it for integration testing, without having to mock anything else :-)
session = OAuth2Session(
    jwk_endpoint=OIDC_JWKS_URL,
    api_logout_url=OIDC_API_LOGOUT_URL,
    client_id=OIDC_CLIENT_ID,
    client_secret=OIDC_CLIENT_SECRET,
)


# The default OpenID Connect backend clients should import and use.
# Makes it easy to switch implementation without effects anywhere else.
oidc_backend = SignaturgruppenBackend(
    session=session,
    authorization_endpoint=OIDC_LOGIN_URL,
    token_endpoint=OIDC_TOKEN_URL,
)

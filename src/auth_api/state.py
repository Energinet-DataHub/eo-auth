from typing import Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from origin.tokens import TokenEncoder
from origin.api import TemporaryRedirect, Cookie
from origin.tools import url_append
from origin.auth import TOKEN_COOKIE_NAME

from auth_api.oidc import OIDC_ERROR_CODES
from auth_api.db import db
from auth_api.models import DbUser
from auth_api.controller import db_controller
from auth_api.config import (
    INTERNAL_TOKEN_SECRET,
    TOKEN_COOKIE_DOMAIN,
    TOKEN_COOKIE_SAMESITE,
    TOKEN_COOKIE_HTTP_ONLY,
    TOKEN_DEFAULT_SCOPES,
    TOKEN_EXPIRY_DELTA,
)


# -- Models ------------------------------------------------------------------


@dataclass
class AuthState:
    """
    AuthState is an intermediate token generated when the user requests
    an authorization URL. It encodes to a [JWT] string.
    The token is included in the authorization URL, and is returned by the
    OIDC Identity Provider when the client is redirected back.
    It provides a way to keep this service stateless.
    """
    fe_url: str
    return_url: str
    terms_accepted: Optional[bool] = field(default=False)
    terms_version: Optional[str] = field(default=None)
    id_token: Optional[str] = field(default=None)
    tin: Optional[str] = field(default=None)
    identity_provider: Optional[str] = field(default=None)
    external_subject: Optional[str] = field(default=None)


# -- Encoders ----------------------------------------------------------------


state_encoder = TokenEncoder(
    schema=AuthState,
    secret=INTERNAL_TOKEN_SECRET,
)


# -- Functions ---------------------------------------------------------------


def build_failure_url(
    state: AuthState,
    error_code: str,
) -> str:
    """
    Builds the URL used for redirecting
    """
    query = {
        'success': '0',
        'error_code': error_code,
        'error': OIDC_ERROR_CODES[error_code],
    }

    # Append (or override) query parameters to the return_url provided
    # by the client, but keep all other query parameters
    return url_append(
        url=state.return_url,
        query_extra=query,
    )


def redirect_to_failure(
    state: AuthState,
    error_code: str,
) -> TemporaryRedirect:
    """
    Creates a 307-redirect to the return_url defined in the state
    with query parameters appended appropriately according to the error.

    :param state: State object
    :param error_code: Internal error code
    :returns: Http response
    """
    return TemporaryRedirect(
        url=build_failure_url(
            state=state,
            error_code=error_code,
        ),
    )


def redirect_to_success(
    state: AuthState,
    session: db.session,
    user: Optional[DbUser],
    id_token: str
) -> TemporaryRedirect:
    """
    After a successful action, redirect to return url with an opaque token
    and success = 1
    """
    db_controller.register_user_login(
        session=session,
        user=user,
    )

    # -- Token -----------------------------------------------------------

    issued = datetime.now(tz=timezone.utc)

    opaque_token = db_controller.create_token(
        session=session,
        issued=issued,
        expires=issued + TOKEN_EXPIRY_DELTA,
        subject=user.subject,
        scope=TOKEN_DEFAULT_SCOPES,
        id_token=id_token,
    )

    # -- Response --------------------------------------------------------

    cookie = Cookie(
        name=TOKEN_COOKIE_NAME,
        value=opaque_token,
        domain=TOKEN_COOKIE_DOMAIN,
        path='/',
        http_only=TOKEN_COOKIE_HTTP_ONLY,
        same_site=TOKEN_COOKIE_SAMESITE,
        secure=True,
    )

    # Append (or override) query parameters to the return_url provided
    # by the client, but keep all other query parameters
    actual_redirect_url = url_append(
        url=state.return_url,
        query_extra={'success': '1'},
    )

    return TemporaryRedirect(
        url=actual_redirect_url,
        cookies=(cookie,),
    )

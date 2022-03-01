# Standard Library
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from xmlrpc.client import Boolean

# First party
from origin.api import (
    Cookie,
    HttpResponse,
    TemporaryRedirect,
)
from origin.auth import TOKEN_COOKIE_NAME
from origin.encrypt import aes256_decrypt
from origin.tokens import TokenEncoder
from origin.tools import url_append

# Local
from config import (
    INTERNAL_TOKEN_SECRET,
    STATE_ENCRYPTION_SECRET,
    TOKEN_COOKIE_DOMAIN,
    TOKEN_COOKIE_HTTP_ONLY,
    TOKEN_COOKIE_SAMESITE,
    TOKEN_COOKIE_PATH,
    TOKEN_DEFAULT_SCOPES,
    TOKEN_EXPIRY_DELTA,
)
from controller import db_controller
from db import db
from models import DbUser
from user import create_or_get_user
from state import AuthState

from oidc import (
    oidc_backend,
)


@dataclass
class LoginResponse:
    """Class to handle the login response."""

    next_url: str
    state: Optional[AuthState] = field(default=None)


@dataclass
class NextStep:
    """
    Internally class for the next step.

    Class used internally to return the next step before being wrapped in
    either a TemporaryRedirect or 200 response.
    """

    next_url: str
    cookie: Optional[Cookie] = field(default=None)


state_encoder = TokenEncoder(
    schema=AuthState,
    secret=INTERNAL_TOKEN_SECRET,
)


class LoginOrchestrator:
    """Orchestrator to handle the login flow."""

    def __init__(
        self,
        state: AuthState,
        session: db.Session,
        user: DbUser = None
    ) -> None:
        self.state = state
        self.session = session
        self.user = user

    def redirect_next_step(
        self
    ) -> TemporaryRedirect:
        """
        Next step for the redirect.

        Redirects the user based on where _get_next_step decides the user is
        in the flow.
        This is used when the backend has full control of where the user is
        going.
        """
        next_step = self._get_next_step()

        if next_step.cookie is not None:
            return TemporaryRedirect(
                url=next_step.next_url,
                cookies=(next_step.cookie,),
            )

        return TemporaryRedirect(
            url=next_step.next_url
        )

    def response_next_step(
        self
    ) -> HttpResponse:
        """
        Return a http response.

        Returns a http response based on where _get_next_step decides the user
        is in the flow.
        This is used in cases where the frontend can't or doesn't accept a
        redirect, e.g. an ajax request.
        """
        next_step = self._get_next_step()

        response = LoginResponse(
            next_url=next_step.next_url,
            state=self.state if next_step.cookie is None else None,
        )

        if next_step.cookie is not None:
            return HttpResponse(
                status=200,
                model=response,
                cookies=(next_step.cookie,)
            )

        return HttpResponse(
            status=200,
            model=response,
        )

    def _get_next_step(
        self
    ) -> NextStep:
        """
        Flow control of the onboarding.

        Based on which values are set we can extrapolate the users
        current position in the onboarding setup
        """
        if self.user is not None:
            return self._return_login_success()

        if not self.state.terms_accepted:
            return NextStep(
                next_url=url_append(
                    url=self.state.fe_url,
                    path_extra='/terms',
                    query_extra={
                        'state': state_encoder.encode(self.state),
                    }
                )
            )

        self.user = create_or_get_user(
            session=self.session,
            state=self.state,
        )

        return self._return_login_success()

    def _return_login_success(
        self
    ) -> NextStep:
        """
        Return URL with opaque token.

        After a successful action, redirect to return url with an opaque token
        and success = 1
        """
        cookie = self._log_in_user_and_create_cookie()

        # Append (or override) query parameters to the return_url provided
        # by the client, but keep all other query parameters
        actual_redirect_url = url_append(
            url=self.state.return_url,
            query_extra={'success': '1'},
        )

        return NextStep(
            next_url=actual_redirect_url,
            cookie=cookie
        )

    def _log_in_user_and_create_cookie(
        self
    ) -> Cookie:
        """
        Register user login and creates cookie.

        Register user login after completed registration and create http only
        cookie.
        """
        db_controller.register_user_login(
            session=self.session,
            user=self.user,
        )

        issued = datetime.now(tz=timezone.utc)

        opaque_token = db_controller.create_token(
            session=self.session,
            issued=issued,
            expires=issued + TOKEN_EXPIRY_DELTA,
            subject=self.user.subject,
            scope=TOKEN_DEFAULT_SCOPES,
            id_token=aes256_decrypt(
                self.state.id_token,
                STATE_ENCRYPTION_SECRET
            ),
        )

        return Cookie(
            name=TOKEN_COOKIE_NAME,
            value=opaque_token,
            domain=TOKEN_COOKIE_DOMAIN,
            path=TOKEN_COOKIE_PATH,
            http_only=TOKEN_COOKIE_HTTP_ONLY,
            same_site=TOKEN_COOKIE_SAMESITE,
            secure=True,
        )

    def invalidate_login(self) -> Boolean:
        """Invalidate an initiated login that is persistented only in state."""
        if self.state is not None and self.state.id_token is not None:
            oidc_backend.logout(self.state.id_token)
            return True

        return False

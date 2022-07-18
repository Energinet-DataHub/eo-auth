# Standard Library
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

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
import requests

# Local
from auth_api.config import (
    DATASYNC_BASE_URL,
    DATASYNC_CREATE_RELATIONS_PATH,
    INTERNAL_TOKEN_SECRET,
    STATE_ENCRYPTION_SECRET,
    TOKEN_COOKIE_DOMAIN,
    TOKEN_COOKIE_HTTP_ONLY,
    TOKEN_COOKIE_SAMESITE,
    TOKEN_COOKIE_PATH,
    TOKEN_DEFAULT_SCOPES,
    TOKEN_EXPIRY_DELTA,
)
from auth_api.controller import db_controller
from auth_api.db import db
from auth_api.models import DbCompany, DbUser
from auth_api.user import create_or_get_user
from auth_api.state import AuthState

from auth_api.oidc import (
    oidc_backend,
)

from auth_api.templates.logging_templates import LoggingTemplates


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
        user: Optional[DbUser] = None,
        company: Optional[DbCompany] = None,
    ) -> None:
        self.state = state
        self.session = session
        self.user = user
        self.company = company

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

        # If user is signed in as a company assign user to company
        if self.state.tin:
            self.company = db_controller.get_or_create_company(
                session=self.session,
                tin=self.state.tin,
            )

            db_controller.attach_user_to_company(
                session=self.session,
                company=self.company,
                user=self.user,
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

    def _create_relations(self, internal_token: str) -> bool:
        """
        Create relationship between user and meteringpoints.

        This is a temporary function to tell the data-sync domain to create
        a relation between the user and it's meteringpoints. This will be
        replaced once the event store is up and running

        :return: Success
        :rtype: bool
        """

        if not self.user and not self.company:
            raise Exception(
                "Failed to create meteringpoint relation. Expected ssn or tin"
            )

        tin = None
        ssn = None

        if self.company is not None and self.company.tin is not None:
            tin = self.company.tin
        elif self.user is not None and self.user.ssn is not None:
            ssn = self.user.ssn
        else:
            raise Exception(
                "Failed to create relationship. Neither tin or ssn were set"
            )

        uri = f'{DATASYNC_BASE_URL}{DATASYNC_CREATE_RELATIONS_PATH}'

        response = requests.post(
            url=uri,
            headers={
                "Authorization": f'Bearer: {internal_token}'
            },
            json={
                "ssn": ssn,
                "tin": tin,
            }
        )

        if response.status_code != 200:
            print(f"Failed to create releation for user {self.user.subject}")
            print(f"'{uri}' Responded with status code {response.status_code}")
        else:
            print(f"created releation for user {self.user.subject}")

    def _log_in_user_and_create_cookie(
        self
    ) -> Cookie:
        """
        Register user login and creates cookie.

        Register user login after completed registration and create http only
        cookie.
        """

        logger = LoggingTemplates(log_level='Information')

        subject = self.user.subject

        # Check if user logged in on behalf of a company
        if self.company:
            subject = self.company.id

        db_controller.register_user_login(
            session=self.session,
            user=self.user,
        )

        issued = datetime.now(tz=timezone.utc)

        opaque_token = db_controller.create_token(
            session=self.session,
            issued=issued,
            expires=issued + TOKEN_EXPIRY_DELTA,
            actor=self.user.subject,
            subject=subject,
            scope=TOKEN_DEFAULT_SCOPES,
            id_token=aes256_decrypt(
                self.state.id_token,
                STATE_ENCRYPTION_SECRET
            ),
        )

        # Get token required to create relations
        token = db_controller.get_token(
            session=self.session,
            opaque_token=opaque_token,
        )

        logger.log(message=f"User {self.state.tin}", actor=self.state.tin,
                   subject=subject)

        # Create relationship between meteringpoints and the user
        self._create_relations(token.internal_token)

        return Cookie(
            name=TOKEN_COOKIE_NAME,
            value=opaque_token,
            domain=TOKEN_COOKIE_DOMAIN,
            path=TOKEN_COOKIE_PATH,
            http_only=TOKEN_COOKIE_HTTP_ONLY,
            same_site=TOKEN_COOKIE_SAMESITE,
            secure=True,
        )

    def invalidate_login(self) -> bool:
        """Invalidate an initiated login that is persistented only in state."""
        if self.state is not None and self.state.id_token is not None:
            oidc_backend.logout(self.state.id_token)
            return True

        return False

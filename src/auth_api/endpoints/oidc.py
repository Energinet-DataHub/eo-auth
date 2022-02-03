from typing import Optional, Any, Union
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

from origin.auth import TOKEN_COOKIE_NAME
from origin.tools import url_append
from origin.api import (
    Endpoint,
    Context,
    HttpResponse,
    TemporaryRedirect,
    Cookie,
    BadRequest,
)

from auth_api.db import db
from auth_api.models import DbUser
from auth_api.controller import db_controller
from auth_api.config import (
    TOKEN_COOKIE_DOMAIN,
    TOKEN_COOKIE_SAMESITE,
    TOKEN_COOKIE_HTTP_ONLY,
    OIDC_LOGIN_CALLBACK_URL,
    TERMS_URL,
    TERMS_ACCEPT_URL,
    TOKEN_EXPIRY_DELTA,
)

from auth_api.oidc import (
    oidc_backend,
    OpenIDConnectToken,
)
from auth_api.queries import UserQuery

from auth_api.state import (
    AuthState, 
    state_encoder, 
    redirect_to_failure,
    redirect_to_success,
)


# -- Models ------------------------------------------------------------------


@dataclass
class OidcCallbackParams:
    """
    Parameters provided by the Identity Provider when redirecting
    clients back to callback endpoints.
    TODO Describe each field separately
    """
    state: Optional[str] = field(default=None)
    iss: Optional[str] = field(default=None)
    code: Optional[str] = field(default=None)
    scope: Optional[str] = field(default=None)
    error: Optional[str] = field(default=None)
    error_hint: Optional[str] = field(default=None)
    error_description: Optional[str] = field(default=None)


# -- Login Endpoints ---------------------------------------------------------


class OpenIdLogin(Endpoint):
    """
    Returns a URL which initiates a login flow @ the
    OpenID Connect Identity Provider.
    """

    @dataclass
    class Request:
        return_url: str
        fe_url: str

    @dataclass
    class Response:
        next_url: Optional[str] = field(default=None)

    def handle_request(
            self,
            request: Request,
    ) -> Union[Response, TemporaryRedirect]:
        """
        Handle HTTP request.
        """
        state = AuthState(
            fe_url=request.fe_url,
            return_url=request.return_url,
        )

        next_url = oidc_backend.create_authorization_url(
            state=state_encoder.encode(state),
            callback_uri=OIDC_LOGIN_CALLBACK_URL,
            validate_ssn=False,
        )

        return self.Response(next_url=next_url)


# -- Login Callback Endpoints ------------------------------------------------


class OpenIDCallbackEndpoint(Endpoint):
    """
    Base-class for OpenID Connect callback endpoints that handles when a
    client is returned from the Identity Provider after either completing
    or interrupting an OpenID Connect authorization flow.

    Inherited classes can implement methods on_oidc_flow_failed()
    and on_oidc_flow_succeeded(), which are invoked depending on the
    result of the flow.
    """

    Request = OidcCallbackParams

    def __init__(self, url: str):
        """
        :param url: Absolute, public URL to this endpoint
        """
        self.url = url

    @db.atomic()
    def handle_request(
            self,
            request: OidcCallbackParams,
            session: db.Session,
    ) -> TemporaryRedirect:
        """
        Handle request.
        """

        # Decode state
        try:
            state = state_encoder.decode(request.state)
        except state_encoder.DecodeError:
            # TODO Handle...
            raise BadRequest()

        # Handle errors from Identity Provider
        if request.error or request.error_description:
            return self.on_oidc_flow_failed(
                state=state,
                params=request,
            )

        # Fetch token from Identity Provider
        try:
            oidc_token = oidc_backend.fetch_token(
                code=request.code,
                state=request.state,
                redirect_uri=self.url,
            )
        except Exception:
            # TODO Log this exception
            return redirect_to_failure(
                state=state,
                error_code='E505',
            )

        # Set values for later use
        state.tin = oidc_token.tin
        state.id_token = oidc_token.id_token
        state.identity_provider = oidc_token.provider
        state.external_subject = oidc_token.subject

        # User is unknown when logging in for the first time and may be None
        user = db_controller.get_user_by_external_subject(
            session=session,
            external_subject=oidc_token.subject,
            identity_provider=oidc_token.provider,
        )

        return self.on_oidc_flow_succeeded(
            session=session,
            state=state,
            token=oidc_token,
            user=user,
        )

    def on_oidc_flow_succeeded(
            self,
            session: db.Session,
            state: AuthState,
            token: OpenIDConnectToken,
            user: Optional[DbUser],
    ) -> TemporaryRedirect:
        """
        Invoked when OpenID Connect flow succeeds, and the client was
        returned to the callback endpoint.

        Note: Inherited classes override this method and add some extra
        logic before it is invoked.

        :param session: Database session
        :param state: OpenID Connect state object
        :param token: OpenID Connect token fetched from Identity Provider
        :param user: The user who just completed the flow, or None if
            the user is not registered in the system
        :returns: HTTP response
        """

        # Inherited classes should make sure this method is only invoked
        # if a user already exists, otherwise something went wrong
        if user is None:
            raise RuntimeError('Can not succeed flow without a user')

        return redirect_to_success(
            state=state,
            session=session,
            user=user,
            id_token=token.id_token,
        )

    def on_oidc_flow_failed(
            self,
            state: AuthState,
            params: OidcCallbackParams,
    ) -> TemporaryRedirect:
        """
        Invoked when OpenID Connect flow fails, and the user was returned to
        the callback endpoint. Redirects clients back to return_uri with
        the necessary query parameters.

        Note: Inherited classes override this method and add some extra
        logic before it is invoked.

        ----------------------------------------------------------------------
        error:                error_description:
        ----------------------------------------------------------------------
        access_denied         mitid_user_aborted
        access_denied         user_aborted
        ----------------------------------------------------------------------

        :param state: State object
        :param params: Callback parameters from Identity Provider
        :returns: Http response
        """
        if params.error_description in ('mitid_user_aborted', 'user_aborted'):
            error_code = 'E1'
        else:
            error_code = 'E0'

        return redirect_to_failure(
            state=state,
            error_code=error_code,
        )


class OpenIDLoginCallback(OpenIDCallbackEndpoint):
    """
    Client is redirected to this callback endpoint after completing
    or interrupting an OpenID Connect authorization flow.

    The user may not be known to the system in case its the first time
    they login. In that case, we redirect them to the terms and conditions.
    """

    def on_oidc_flow_succeeded(
            self,
            session: db.Session,
            state: AuthState,
            token: OpenIDConnectToken,
            user: Optional[DbUser],
    ) -> Any:
        """
        Invoked when OpenID Connect flow succeeds, and the client was
        returned to the callback endpoint.

        :param session: Database session
        :param state: OpenID Connect state object
        :param token: OpenID Connect token fetched from Identity Provider
        :param user: The user who just completed the flow, or None if
            the user is not registered in the system
        :returns: HTTP response
        """

        if user is None:
            return TemporaryRedirect(
                url=url_append(
                    url=state.fe_url,
                    path_extra='/terms',
                    query_extra={
                        'state': state_encoder.encode(state),
                        'terms_url': TERMS_URL,
                        'terms_accept_url': TERMS_ACCEPT_URL,
                    }
                )
            )

        return super(OpenIDLoginCallback, self).on_oidc_flow_succeeded(
            session=session,
            state=state,
            token=token,
            user=user,
        )


class CreateUser(Endpoint):
    """
    Attempts to create a user if it doesn't exist and the terms and conditions
    have been accepted, then redirects to return_url.
    """

    @dataclass
    class Request:
        state: str

    @db.atomic()
    def handle_request(
            self,
            session: db.Session,
            request: Request,
    ) -> TemporaryRedirect:
        """
        Handle HTTP request.
        """
        # Decode state
        try:
            state = state_encoder.decode(request.state)
        except state_encoder.DecodeError:
            # TODO Handle...
            raise BadRequest()

        if not state.terms_accepted:
            return redirect_to_failure(
                state=state,
                error_code='E4',
            )

        user = db_controller.get_or_create_user(
            session=session,
            tin=state.tin,
        )

        db_controller.attach_external_user(
            session=session,
            user=user,
            external_subject=state.external_subject,
            identity_provider=state.identity_provider,
        )

        return redirect_to_success(
            state=state,
            session=session,
            user=user,
            id_token=state.id_token,
        )


# -- Logout Endpoints --------------------------------------------------------


class OpenIdLogout(Endpoint):
    """
    Returns a logout URL which initiates a logout flow @ the
    OpenID Connect Identity Provider.
    """

    @dataclass
    class Response:
        success: bool

    @db.atomic()
    def handle_request(
            self,
            context: Context,
            session: db.Session,
    ) -> HttpResponse:
        """
        Handle HTTP request.
        """
        token = db_controller.get_token(
            session=session,
            opaque_token=context.opaque_token,
            only_valid=False,
        )

        if token is not None:
            session.delete(token)
            oidc_backend.logout(token.id_token)
            session.commit()

        cookie = Cookie(
            name=TOKEN_COOKIE_NAME,
            value='',
            path='/',
            domain=TOKEN_COOKIE_DOMAIN,
            http_only=TOKEN_COOKIE_HTTP_ONLY,
            same_site=TOKEN_COOKIE_SAMESITE,
            secure=True,
            expires=datetime.now(tz=timezone.utc),
        )

        return HttpResponse(
            status=200,
            cookies=(cookie,),
            model=self.Response(success=True),
        )

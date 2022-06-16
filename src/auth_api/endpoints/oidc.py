from typing import Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field

from origin.auth import TOKEN_COOKIE_NAME
from origin.encrypt import aes256_encrypt
from origin.api import (
    Endpoint,
    Context,
    HttpResponse,
    TemporaryRedirect,
    Cookie,
    BadRequest,
)

from auth_api.db import db
from auth_api.controller import db_controller
from auth_api.orchestrator import LoginOrchestrator, state_encoder
from auth_api.state import AuthState, redirect_to_failure
from auth_api.config import (
    TOKEN_COOKIE_DOMAIN,
    TOKEN_COOKIE_SAMESITE,
    TOKEN_COOKIE_HTTP_ONLY,
    TOKEN_COOKIE_PATH,
    OIDC_LOGIN_CALLBACK_URL,
    STATE_ENCRYPTION_SECRET,
    OIDC_LANGUAGE,
)
from auth_api.oidc import (
    oidc_backend,
)


# -- Models ------------------------------------------------------------------


@dataclass
class OidcCallbackParams:
    """
    HTTP Payload parsed by Identity Provider.

    Parameters provided by the Identity Provider when redirecting
    clients back to callback endpoints.

    :param state: OpenID Connect state object
    :param iss: Identifier for the issuer as an URL.
    :param code: Response type
    :param scope: OpenID Connect scopes ('openid', 'mitid', 'nemid', ...)
    :param error: Error response.
    :param error_hint: Text hint of the error.
    :param error_description: Text description of the error.
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
    HTTP Endpoint which starts the whole login flow.

    Return a URL which initiates a login flow @ the
    OpenID Connect Identity Provider.
    """

    @dataclass
    class Request:
        """The HTTP request payload."""

        return_url: str
        fe_url: str

    @dataclass
    class Response:
        """The HTTP response body."""

        next_url: Optional[str] = field(default=None)

    def handle_request(
            self,
            request: Request,
    ) -> Union[Response, TemporaryRedirect]:
        """Handle HTTP request."""

        state = AuthState(
            fe_url=request.fe_url,
            return_url=request.return_url,
        )

        next_url = oidc_backend.create_authorization_url(
            state=state_encoder.encode(state),
            callback_uri=OIDC_LOGIN_CALLBACK_URL,
            validate_ssn=False,
            language=OIDC_LANGUAGE,
        )

        return self.Response(next_url=next_url)


# -- Login Callback Endpoints ------------------------------------------------


class OpenIDCallbackEndpoint(Endpoint):
    """
    HTTP Endpoint for handling users completing or interrupting OIDC Auth flow.

    Base-class for OpenID Connect callback endpoints that handles when a
    client is returned from the Identity Provider after either completing
    or interrupting an OpenID Connect authorization flow.
    Inherited classes can implement methods on_oidc_flow_failed()
    and on_oidc_flow_succeeded(), which are invoked depending on the
    result of the flow.

    :param url: Absolute, public URL to this endpoint.
    """

    Request = OidcCallbackParams

    def __init__(self, url: str):
        self.url = url

    @db.atomic()
    def handle_request(
            self,
            request: OidcCallbackParams,
            session: db.Session,
    ) -> TemporaryRedirect:
        """
        Handle request.

        :param request: Parameters provided by the Identity Provider
        :param session: Database session
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
        except Exception as e:
            print(e)
            # TODO Log this exception
            return redirect_to_failure(
                state=state,
                error_code='E505',
            )

        print("oidc_token.is_private", oidc_token.is_private)
        print("oidc_token.is_company", oidc_token.is_company)
        print("oidc_token.tin", oidc_token.tin)
        print("oidc_token.ssn is set", oidc_token.ssn is not None)
        print("oidc_token.subject", oidc_token.subject)

        if oidc_token.is_private:
            print("Tried to login as a private user which isn't supported")
            return redirect_to_failure(
                state=state,
                error_code='E504',
            )


        # Set values for later use
        state.tin = oidc_token.tin
        state.identity_provider = oidc_token.provider
        state.external_subject = oidc_token.subject
        state.id_token = aes256_encrypt(
            data=oidc_token.id_token,
            key=STATE_ENCRYPTION_SECRET,
        )

        # User is unknown when logging in for the first time and may be None
        user = db_controller.get_user_by_external_subject(
            session=session,
            external_subject=oidc_token.subject,
            identity_provider=oidc_token.provider,
        )

        company = None
        if oidc_token.tin:
            company = db_controller.get_company_by_tin(
                session=session,
                tin=oidc_token.tin,
            )

        orchestrator = LoginOrchestrator(
            session=session,
            state=state,
            user=user,
            company=company,
        )

        return orchestrator.redirect_next_step()

    def on_oidc_flow_failed(
            self,
            state: AuthState,
            params: OidcCallbackParams,
    ) -> TemporaryRedirect:
        """
        Invoke when OpenID Connect Flow fails.

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


# -- Logout Endpoints --------------------------------------------------------


class OpenIdLogout(Endpoint):
    """
    OpenID Logout endpoint which logs the user out.

    Logs out the user from both our system as well as the used
    OpenId Connect Identity Provider. This is done by calling the OIDC
    logout endpoint as well as deleting the OIDC login session.
    """

    @dataclass
    class Response:
        """The HTTP response body."""

        success: bool

    @db.atomic()
    def handle_request(
            self,
            context: Context,
            session: db.Session,
    ) -> HttpResponse:
        """
        Handle HTTP request.

        :param context: Context for a single HTTP request.
        :param session: Database session.
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
            path=TOKEN_COOKIE_PATH,
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


class OpenIdInvalidateLogin(Endpoint):
    """Returns a URL which invalidates a login."""

    @dataclass
    class Response:
        """The HTTP response body."""

        success: bool

    @dataclass
    class Request:
        """The HTTP request body."""

        state: str

    def handle_request(
            self,
            request: Request,
    ) -> HttpResponse:
        """Handle HTTP request."""

        try:
            state = state_encoder.decode(request.state)
        except state_encoder.DecodeError:
            raise BadRequest()

        orchestrator = LoginOrchestrator(
            state=state,
            session=None
        )

        if not orchestrator.invalidate_login():
            raise BadRequest()

        return HttpResponse(
            status=200,
            model=self.Response(success=True),
        )

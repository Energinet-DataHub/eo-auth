from typing import Optional, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field

from energytt_platform.tokens import TokenEncoder
from energytt_platform.auth import TOKEN_COOKIE_NAME
from energytt_platform.tools import append_query_parameters
from energytt_platform.api import (
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
    INTERNAL_TOKEN_SECRET,
    TOKEN_COOKIE_DOMAIN,
    TOKEN_DEFAULT_SCOPES,
    OIDC_LOGIN_CALLBACK_URL,
    OIDC_SSN_VALIDATE_CALLBACK_URL,
)

from .errors import ERROR_CODES
from .models import AuthState, OidcCallbackParams
from .signaturgruppen import oidc, OpenIDConnectToken


# -- Encoders ----------------------------------------------------------------


state_encoder = TokenEncoder(
    schema=AuthState,
    secret=INTERNAL_TOKEN_SECRET,
)


# -- Login Endpoints ---------------------------------------------------------


class OpenIdLogin(Endpoint):
    """
    Creates a URL which initiates a login flow @ the OpenID Connect
    Identity Provider. If the 'redirect' parameter is provided,
    the endpoint 307 redirects the client, otherwise it returns the
    URL as JSON body.
    """

    @dataclass
    class Request:
        return_url: str
        redirect: Optional[str] = field(default=None)

    @dataclass
    class Response:
        url: Optional[str] = field(default=None)

    def handle_request(
            self,
            request: Request,
    ) -> Union[Response, TemporaryRedirect]:
        """
        Handle HTTP request.
        """
        state = AuthState(
            return_url=request.return_url,
        )

        url = oidc.create_authorization_url(
            state=state_encoder.encode(state),
            callback_uri=OIDC_LOGIN_CALLBACK_URL,
            validate_ssn=False,
        )

        if request.redirect:
            return TemporaryRedirect(url=url)
        else:
            return self.Response(url=url)


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
            token = oidc.fetch_token(
                code=request.code,
                state=request.state,
                redirect_uri=self.url,
            )
        except:
            # TODO Log this exception
            return self._redirect_to_failure(
                state=state,
                error_code='E505',
            )

        # User is unknown when logging in for the first time and may be None
        user = db_controller.get_user_by_external_subject(
            session=session,
            external_subject=token.subject,
            identity_provider=token.identity_provider,
        )

        return self.on_oidc_flow_succeeded(
            session=session,
            state=state,
            token=token,
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

        # -- User ------------------------------------------------------------

        db_controller.register_user_login(
            session=session,
            user=user,
        )

        # -- Token -----------------------------------------------------------

        opaque_token = db_controller.create_token(
            session=session,
            issued=token.issued,
            expires=token.expires,
            subject=user.subject,
            scope=TOKEN_DEFAULT_SCOPES,
            id_token=token.id_token_raw,
        )

        # -- Response --------------------------------------------------------

        cookie = Cookie(
            name=TOKEN_COOKIE_NAME,
            value=opaque_token,
            domain=TOKEN_COOKIE_DOMAIN,
            http_only=True,
            same_site=True,
            secure=True,
        )

        # Append (or override) query parameters to the return_url provided
        # by the client, but keep all other query parameters
        actual_redirect_url = append_query_parameters(
            url=state.return_url,
            query_extra={'success': '1'},
        )

        return TemporaryRedirect(
            url=actual_redirect_url,
            cookies=(cookie,),
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

        return self._redirect_to_failure(
            state=state,
            error_code=error_code,
        )

    def _redirect_to_failure(
            self,
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
        query = {
            'success': '0',
            'error_code': error_code,
            'error': ERROR_CODES[error_code],
        }

        # Append (or override) query parameters to the return_url provided
        # by the client, but keep all other query parameters
        actual_redirect_url = append_query_parameters(
            url=state.return_url,
            query_extra=query,
        )

        return TemporaryRedirect(
            url=actual_redirect_url,
        )


class OpenIDLoginCallback(OpenIDCallbackEndpoint):
    """
    Client is redirected to this callback endpoint after completing
    or interrupting an OpenID Connect authorization flow.

    The user may not be known to the system in case its the first time
    they login. In this case, we initiate another OpenID Connect flow,
    but this time requesting social security number. After completing this
    second flow, the user is redirected back to OpenIdSsnCallback-endpoint.
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
            # If the user is not known by the Identity Provider's subject,
            # we initiate a new OpenID Connect authorization flow, but this
            # time requesting the user's social security number.
            # This flow results in a callback to the OpenIDSsnCallback
            # endpoint (below).
            return TemporaryRedirect(
                url=oidc.create_authorization_url(
                    state=state_encoder.encode(state),
                    callback_uri=OIDC_SSN_VALIDATE_CALLBACK_URL,
                    validate_ssn=True,
                ),
            )

        return super(OpenIDLoginCallback, self).on_oidc_flow_succeeded(
            session=session,
            state=state,
            token=token,
            user=user,
        )


class OpenIDSsnCallback(OpenIDCallbackEndpoint):
    """
    Client is redirected to this callback endpoint after completing
    or interrupting an OpenID Connect SSN verification flow.

    The user may not be known to the system in case its the first time
    they login. In this case, we create the user locally.

    Afterwards, the client is redirected back to it's return_uri.
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
            user = db_controller.get_or_create_user(
                session=session,
                ssn=token.ssn,
            )

            db_controller.attach_external_user(
                session=session,
                user=user,
                identity_provider=token.identity_provider,
                external_subject=token.subject,
            )

        return super(OpenIDSsnCallback, self).on_oidc_flow_succeeded(
            session=session,
            state=state,
            token=token,
            user=user,
        )


# -- Logout Endpoints --------------------------------------------------------


class OpenIdLogout(Endpoint):
    """
    Returns a logout URL which initiates a logout flow @ the
    OpenID Connect Identity Provider.
    """

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
            oidc.logout(token.id_token)

        cookie = Cookie(
            name=TOKEN_COOKIE_NAME,
            value='',
            domain=TOKEN_COOKIE_DOMAIN,
            http_only=True,
            same_site=True,
            secure=True,
            expires=datetime.now(tz=timezone.utc),
        )

        return HttpResponse(
            status=200,
            cookies=(cookie,),
        )

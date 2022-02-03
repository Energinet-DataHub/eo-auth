from origin.api import Application, TokenGuard

from .config import (
    INTERNAL_TOKEN_SECRET,
    OIDC_LOGIN_CALLBACK_PATH,
    OIDC_LOGIN_CALLBACK_URL,
    TERMS_PATH,
    TERMS_ACCEPT_PATH,
    CREATE_USER_PATH,
)

from .endpoints import (
    # OpenID Connect:
    OpenIdLogin,
    OpenIDLoginCallback,
    OpenIdLogout,
    # Profiles:
    GetProfile,
    # Tokens:
    ForwardAuth,
    InspectToken,
    CreateTestToken,
    # Terms:
    GetTerms,
    AcceptTerms,
    # Users:
    CreateUser,
)


def create_app() -> Application:
    """
    Creates a new instance of the application.
    """

    app = Application.create(
        name='Auth API',
        secret=INTERNAL_TOKEN_SECRET,
        health_check_path='/health',
    )

    # -- OpenID Connect Login ------------------------------------------------

    # Login
    app.add_endpoint(
        method='GET',
        path='/oidc/login',
        endpoint=OpenIdLogin(),
    )

    # Callback, after logging in
    app.add_endpoint(
        method='GET',
        path=OIDC_LOGIN_CALLBACK_PATH,
        endpoint=OpenIDLoginCallback(url=OIDC_LOGIN_CALLBACK_URL),
    )

    # -- OpenID Connect Logout -----------------------------------------------

    app.add_endpoint(
        method='POST',
        path='/logout',
        endpoint=OpenIdLogout(),
        guards=[TokenGuard()],
    )

    # -- Profile(s) ----------------------------------------------------------

    app.add_endpoint(
        method='GET',
        path='/profile',
        endpoint=GetProfile(),
        guards=[TokenGuard()],
    )

    # -- Træfik integration --------------------------------------------------

    app.add_endpoint(
        method='GET',
        path='/token/forward-auth',
        endpoint=ForwardAuth(),
    )

    # -- Testing/misc --------------------------------------------------------

    app.add_endpoint(
        method='GET',
        path='/token/inspect',
        endpoint=InspectToken(),
    )

    app.add_endpoint(
        method='POST',
        path='/token/create-test-token',
        endpoint=CreateTestToken(),
    )

    # -- Terms ---------------------------------------------------------------

    app.add_endpoint(
        method='GET',
        path=TERMS_PATH,
        endpoint=GetTerms(),
    )

    app.add_endpoint(
        method='POST',
        path=TERMS_ACCEPT_PATH,
        endpoint=AcceptTerms(),
    )

    # -- Users ---------------------------------------------------------------

    app.add_endpoint(
        method='POST',
        path=CREATE_USER_PATH,
        endpoint=CreateUser(),
    )

    return app

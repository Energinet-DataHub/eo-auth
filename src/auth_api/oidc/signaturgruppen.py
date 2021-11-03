import requests
from authlib.jose import jwt
from authlib.integrations.requests_client import \
    OAuth2Session as OAuth2Session_

from energytt_platform.serialize import simple_serializer

from auth_api.config import (
    DEBUG,
    OIDC_CLIENT_ID,
    OIDC_CLIENT_SECRET,
    OIDC_LOGIN_URL,
    OIDC_TOKEN_URL,
    OIDC_JWKS_URL,
    OIDC_API_LOGOUT_URL,
)

from .models import (
    OpenIDConnectToken,
    IdToken,
    UserInfoToken,
)


# -- OpenID Connect ----------------------------------------------------------


class OAuth2Session(OAuth2Session_):
    """
    Abstracting low-level OAuth2 actions to simplify testing.
    """
    def get_jwk(self) -> str:
        """
        TODO Cache result in a period
        """
        jwks_response = requests.get(
            url=OIDC_JWKS_URL,
            verify=not DEBUG,
        )

        return jwks_response.content.decode()

    def logout(self, id_token: str):
        """
        Provided an ID-token, this method invokes the back-channel logout
        endpoint on the Identity Provider, which logs the user out on
        their side, forcing the user to login again next time he is
        redirected to the authorization URL.
        """
        response = requests.post(
            url=OIDC_API_LOGOUT_URL,
            json={'id_token': id_token},
        )

        if response.status_code != 200:
            raise RuntimeError(
                f'Logout returned status {response.status_code}')


class SignaturgruppenBackend(object):
    """
    TODO
    """

    def __init__(self):
        """
        TODO
        """
        self.session = OAuth2Session(
            client_id=OIDC_CLIENT_ID,
            client_secret=OIDC_CLIENT_SECRET,
        )

    def create_authorization_url(
            self,
            state: str,
            callback_uri: str,
            validate_ssn: bool,
    ) -> str:
        """
        Creates and returns an absolute URL to initiate an OpenID Connect
        authorization flow at the Identity Provider.

        :param state: An arbitrary string passed to the callback endpoint
        :param callback_uri: URL to callback endpoint to return client to
            after completing or interrupting the flow
        :param validate_ssn: Whether or not to validate social security
            number as part of the flow
        :returns: Absolute URL @ Identity Provider
        """
        if validate_ssn:
            scope = ('openid', 'mitid', 'nemid', 'ssn', 'userinfo_token')
        else:
            scope = ('openid', 'mitid', 'nemid')

        url, _ = self.session.create_authorization_url(
            url=OIDC_LOGIN_URL,
            redirect_uri=callback_uri,
            state=state,
            scope=scope,
        )

        return url

    def fetch_token(
            self,
            code: str,
            state: str,
            redirect_uri: str,
    ) -> OpenIDConnectToken:
        """
        TODO
        """
        token_raw = self.session.fetch_token(
            url=OIDC_TOKEN_URL,
            grant_type='authorization_code',
            code=code,
            state=state,
            redirect_uri=redirect_uri,
            verify=not DEBUG,
        )

        # TODO Test these:
        scope = [s for s in token_raw.get('scope', '').split(' ') if s]

        id_token = self.parse_id_token(token_raw['id_token'])

        token = OpenIDConnectToken(
            scope=scope,
            expires_at=token_raw['expires_at'],
            id_token=id_token,
            id_token_raw=token_raw['id_token'],
        )

        if token_raw.get('userinfo_token'):
            # Parse UserInfo Token
            token.userinfo_token = \
                self.parse_userinfo_token(token_raw['userinfo_token'])

        return token

    def parse_id_token(self, id_token: str) -> IdToken:
        """
        TODO
        """
        raw_token = jwt.decode(
            s=id_token,
            key=self.session.get_jwk(),
        )

        return simple_serializer.deserialize(
            schema=IdToken,
            data=dict(raw_token),
            validate=False,
        )

    def parse_userinfo_token(self, userinfo_token: str) -> UserInfoToken:
        """
        TODO
        """
        raw_token = jwt.decode(
            s=userinfo_token,
            key=self.session.get_jwk(),
        )

        return simple_serializer.deserialize(
            schema=UserInfoToken,
            data=dict(raw_token),
            validate=False,
        )

    def logout(self, id_token: str):
        """
        Provided an ID-token, this method invokes the back-channel logout
        endpoint on the Identity Provider, which logs the user out on
        their side, forcing the user to login again next time he is
        redirected to the authorization URL.
        """
        self.session.logout(id_token)


# -- Singletons --------------------------------------------------------------


oidc = SignaturgruppenBackend()

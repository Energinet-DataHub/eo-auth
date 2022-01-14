import requests
from authlib.integrations.requests_client import \
    OAuth2Session as _OAuth2Session


class OAuth2Session(_OAuth2Session):
    """
    Adds a few useful methods to the default OAuth2Session from authlib.
    """
    def __init__(
            self,
            jwk_endpoint: str,
            api_logout_url: str,
            **kwargs,
    ):
        """
        TODO
        """
        self.jwk_endpoint = jwk_endpoint
        self.api_logout_url = api_logout_url
        super(OAuth2Session, self).__init__(**kwargs)

    def get_jwk(self) -> str:
        """
        TODO Cache result in a period
        """
        jwks_response = requests.get(
            url=self.jwk_endpoint,
            verify=True,
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
            url=self.api_logout_url,
            json={'id_token': id_token},
        )

        if response.status_code != 200:
            raise RuntimeError(
                f'Logout returned status {response.status_code}')

from auth_api.config import DEBUG

from ..backend import OpenIDConnectBackend

from .models import SignaturgruppenToken


class SignaturgruppenBackend(OpenIDConnectBackend):
    """
    TODO
    """
    def __init__(
            self,
            *args,
            authorization_endpoint: str,
            token_endpoint: str,
            **kwargs,
    ):
        """
        TODO
        """
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        super(SignaturgruppenBackend, self).__init__(*args, **kwargs)

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
        scope = ['openid', 'mitid', 'nemid', 'userinfo_token']

        if validate_ssn:
            scope.append('ssn')

        url, _ = self.session.create_authorization_url(
            url=self.authorization_endpoint,
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
    ) -> SignaturgruppenToken:
        """
        TODO
        """
        raw_token = self.session.fetch_token(
            url=self.token_endpoint,
            grant_type='authorization_code',
            code=code,
            state=state,
            redirect_uri=redirect_uri,
            verify=not DEBUG,
        )

        return SignaturgruppenToken.from_raw_token(
            raw_token=raw_token,
            jwk=self.session.get_jwk(),
        )

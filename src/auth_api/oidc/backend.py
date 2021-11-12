from abc import abstractmethod

from .session import OAuth2Session
from .models import OpenIDConnectToken


class OpenIDConnectBackend(object):

    def __init__(self, session: OAuth2Session):
        """
        TODO
        """
        self.session = session

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def fetch_token(
            self,
            code: str,
            state: str,
            redirect_uri: str,
    ) -> OpenIDConnectToken:
        """
        TODO
        """
        raise NotImplementedError

    def logout(self, id_token: str):
        """
        Provided an ID-token, this method invokes the back-channel logout
        endpoint on the Identity Provider, which logs the user out on
        their side, forcing the user to login again next time he is
        redirected to the authorization URL.
        """
        self.session.logout(id_token)

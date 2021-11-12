from typing import Dict, Any
from unittest.mock import MagicMock
from flask.testing import FlaskClient

from energytt_platform.tokens import TokenEncoder
from energytt_platform.api.testing import (
    assert_base_url,
    assert_query_parameter,
)

from auth_api.db import db
from auth_api.endpoints import AuthState
from auth_api.config import (
    OIDC_LOGIN_CALLBACK_PATH,
    OIDC_LOGIN_URL,
    OIDC_SSN_VALIDATE_CALLBACK_URL,
    OIDC_CLIENT_ID,
)


class TestOidcLoginCallbackSubjectUnknown:
    """
    Tests cases where returning to login callback, and the Identity
    Provider's subject is unknown to the system.
    """

    def test__user_does_not_exist__should_redirect_to_verify_ssn(
            self,
            client: FlaskClient,
            mock_session: db.Session,
            mock_get_jwk: MagicMock,
            mock_fetch_token: MagicMock,
            state_encoder: TokenEncoder[AuthState],
            jwk_public: str,
            ip_token: Dict[str, Any],
    ):
        """
        After logging in, if the system does not recognize the Identity
        Provider's subject, it should initiate a new authorization flow at
        the Identity Provider, but this time request the user to verify
        social security number.

        :param client: API client
        :param mock_session: Mocked database session
        :param mock_get_jwk: Mocked get_jwk() method @ OAuth2Session object
        :param mock_fetch_token: Mocked fetch_token() method @ OAuth2Session object
        :param state_encoder: AuthState encoder
        :param jwk_public: Mocked public key from Identity Provider
        :param ip_token: Mocked token from Identity Provider (unencoded)
        """

        # -- Arrange ---------------------------------------------------------

        state = AuthState(return_url='http://redirect-here.com/foobar')
        state_encoded = state_encoder.encode(state)

        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act -------------------------------------------------------------

        r = client.get(
            path=OIDC_LOGIN_CALLBACK_PATH,
            query_string={'state': state_encoded},
        )

        # -- Assert ----------------------------------------------------------

        redirect_location = r.headers['Location']

        assert r.status_code == 307

        # Redirect to Identity Provider should be to correct URL (without
        # taking query parameters into consideration)
        assert_base_url(
            url=redirect_location,
            expected_base_url=OIDC_LOGIN_URL,
            check_path=True,
        )

        # Redirect to Identity Provider must have correct client_id
        assert_query_parameter(
            url=redirect_location,
            name='client_id',
            value=OIDC_CLIENT_ID,
        )

        # Redirect to Identity Provider must have correct redirect_uri,
        # in this case the verify SSN callback endpoint
        assert_query_parameter(
            url=redirect_location,
            name='redirect_uri',
            value=OIDC_SSN_VALIDATE_CALLBACK_URL,
        )

        # Redirect to Identity Provider must have correct scope
        assert_query_parameter(
            url=redirect_location,
            name='scope',
            value='openid mitid nemid userinfo_token ssn',
        )

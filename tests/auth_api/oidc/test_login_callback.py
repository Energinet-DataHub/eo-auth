import pytest

from typing import Dict, Any
from unittest.mock import MagicMock
from flask.testing import FlaskClient
from urllib.parse import parse_qs, urlsplit

from origin.encrypt import aes256_decrypt
from origin.tokens import TokenEncoder
from origin.api.testing import (
    assert_base_url,
    assert_query_parameter,
)

from auth_api.db import db
from auth_api.endpoints import AuthState
from auth_api.config import (
    OIDC_LOGIN_CALLBACK_PATH,
    SSN_ENCRYPTION_KEY,
    TERMS_URL,
    TERMS_ACCEPT_URL,
)


class TestOidcLoginCallbackSubjectUnknown:
    """
    Tests cases where returning to login callback, and the Identity
    Provider's subject is unknown to the system.
    """

    @pytest.mark.integrationtest
    def test__user_does_not_exist__should_redirect_to_terms(
        self,
        client: FlaskClient,
        mock_session: db.Session,
        mock_get_jwk: MagicMock,
        mock_fetch_token: MagicMock,
        state_encoder: TokenEncoder[AuthState],
        jwk_public: str,
        ip_token: Dict[str, Any],
        token_tin: str,
        token_idp: str,
        token_subject: str,
        id_token_encrypted: str,
    ):
        """
        After logging in, if the system does not recognize the Identity
        Provider's subject, it should initiate a new authorization flow at
        the Identity Provider, but this time request the user to verify
        social security number.

        :param client: API client
        :param mock_session: Mocked database session
        :param mock_get_jwk: Mocked get_jwk() method @ OAuth2Session object
        :param mock_fetch_token: Mocked fetch_token() method @ OAuth2Session 
               object
        :param state_encoder: AuthState encoder
        :param jwk_public: Mocked public key from Identity Provider
        :param ip_token: Mocked token from Identity Provider (unencoded)
        """

        # -- Arrange ---------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar')
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

        url = urlsplit(redirect_location)
        query = parse_qs(url.query)
        state_decoded = state_encoder.decode(query['state'][0])

        state_decoded.id_token = aes256_decrypt(
            state_decoded.id_token,
            SSN_ENCRYPTION_KEY
        )

        assert expected_state == state_decoded

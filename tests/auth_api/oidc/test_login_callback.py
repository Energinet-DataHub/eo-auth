# Standard Library
from typing import Any, Dict
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlsplit

# Third party
import pytest
import requests_mock
from flask.testing import FlaskClient

# First party
from origin.api.testing import assert_base_url
from origin.encrypt import aes256_decrypt
from origin.tokens import TokenEncoder

# Local
from auth_api.config import (
    OIDC_LOGIN_CALLBACK_PATH,
    STATE_ENCRYPTION_SECRET,
)
from auth_api.db import db
from auth_api.endpoints import AuthState
from auth_api.queries import CompanyQuery, UserQuery


class TestOidcLoginCallbackSubjectUnknown:
    """
    Tests cases where returning to login callback.

    This also includes when the Identity Provider's subject
    is unknown to the system.
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
        User does not exists and should redirect to verify ssn.

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

        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
        )

        expected_state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            tin=token_tin,
            id_token=ip_token['id_token'],
            identity_provider=token_idp,
            external_subject=token_subject
        )

        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        res = client.get(
            path=OIDC_LOGIN_CALLBACK_PATH,
            query_string={'state': state_encoder.encode(state)},
        )

        # -- Assert -----------------------------------------------------------

        redirect_location = res.headers['Location']

        assert res.status_code == 307

        # Redirect to terms should be to correct URL (without
        # taking query parameters into consideration)
        assert_base_url(
            url=redirect_location,
            expected_base_url='https://foobar.com/terms',
            check_path=True,
        )

        url = urlsplit(redirect_location)
        query = parse_qs(url.query)
        state_decoded = state_encoder.decode(query['state'][0])

        state_decoded.id_token = aes256_decrypt(
            state_decoded.id_token,
            STATE_ENCRYPTION_SECRET
        )

        assert expected_state == state_decoded


class TestOidcLoginCallbackCreateRelations:
    """
    Test that the callback endpoint creates relations.

    One of the responsibilities of the LoginCallback endpoint is to
    tell the datasync service to make relations between a user and the user's
    meteringpoints. This is done by calling the datasync service. This section
    tests that this endpoint actually calls datasync as expected.
    """

    @pytest.mark.integrationtest
    def test__user_does_not_exist__should_call_datasync_create_relations_endpoint(  # noqa: E501
        self,
        client: FlaskClient,
        mock_session: db.Session,
        requests_mock: requests_mock.Adapter,
        mock_get_jwk: MagicMock,
        mock_fetch_token: MagicMock,
        state_encoder: TokenEncoder[AuthState],
        jwk_public: str,
        ip_token: Dict[str, Any],
        token_tin: str,
    ):
        """
        User does not exist and should call datasync create relations endpoint.

        During creating of user and company the endpoint should, call the
        datasync service in order to create relations between the user
        and the user's meteringpoitns.

        :param client: API client
        :param requests_mock: Mocked datasync endpoint
        :param mock_get_jwk: Mocked get_jwk() method @ OAuth2Session object
        :param mock_fetch_token: Mocked fetch_token() method @ OAuth2Session
               object
        :param state_encoder: AuthState encoder
        :param jwk_public: Mocked public key from Identity Provider
        :param ip_token: Mocked token from Identity Provider (unencoded)
        :param token_tin: The tin returned by the OIDC provider
        """

        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            terms_accepted=True,
        )

        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        expected_datasync_request_body = {
            'tin': token_tin,
            'ssn': None
        }

        # -- Act --------------------------------------------------------------

        client.get(
            path=OIDC_LOGIN_CALLBACK_PATH,
            query_string={'state': state_encoder.encode(state)},
        )

        # -- Assert -----------------------------------------------------------

        assert requests_mock.call_count == 1
        assert requests_mock.request_history[0].json() == \
            expected_datasync_request_body

    @pytest.mark.integrationtest
    def test__user_does_not_exist__should_create_new_user_in_database(  # noqa: E501
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
        User does not exist and should call datasync create relations endpoint.

        During creating of user and company the endpoint should, a new user
        should be created in the database.

        :param client: API client
        :param requests_mock: Mocked datasync endpoint
        :param mock_get_jwk: Mocked get_jwk() method @ OAuth2Session object
        :param mock_fetch_token: Mocked fetch_token() method @ OAuth2Session
               object
        :param state_encoder: AuthState encoder
        :param jwk_public: Mocked public key from Identity Provider
        :param ip_token: Mocked token from Identity Provider (unencoded)
        """

        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            terms_accepted=True,
        )

        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        client.get(
            path=OIDC_LOGIN_CALLBACK_PATH,
            query_string={'state': state_encoder.encode(state)},
        )

        # -- Assert -----------------------------------------------------------

        query = UserQuery(mock_session)

        assert query.count() == 1

    @pytest.mark.integrationtest
    def test__company_does_not_exist__should_create_new_company_in_database(  # noqa: E501
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
        Company do not exist and should call datasync create relation endpoint.

        During creating of the user and company the endpoint should, a new
        company should be created in the database.

        :param client: API client
        :param requests_mock: Mocked datasync endpoint
        :param mock_get_jwk: Mocked get_jwk() method @ OAuth2Session object
        :param mock_fetch_token: Mocked fetch_token() method @ OAuth2Session
               object
        :param state_encoder: AuthState encoder
        :param jwk_public: Mocked public key from Identity Provider
        :param ip_token: Mocked token from Identity Provider (unencoded)
        """

        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            terms_accepted=True,
        )

        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        client.get(
            path=OIDC_LOGIN_CALLBACK_PATH,
            query_string={'state': state_encoder.encode(state)},
        )

        # -- Assert -----------------------------------------------------------

        query = CompanyQuery(mock_session)

        assert query.count() == 1

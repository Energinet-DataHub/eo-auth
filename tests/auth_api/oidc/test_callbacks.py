"""
All OIDC callback endpoints have a few things in common. They interpret
query parameters (passed on by the Identity Provider) identically, thus
should also act identically for some cases.

Thus, tests in this file are generic across all OIDC callback endpoints,
and are therefore tested on all of those endpoints.
"""
import pytest
from typing import Dict, Any
from unittest.mock import MagicMock
from flask.testing import FlaskClient
from datetime import datetime, timezone

from origin.tokens import TokenEncoder
from origin.auth import TOKEN_COOKIE_NAME, TOKEN_HEADER_NAME
from origin.api.testing import (
    CookieTester,
    assert_base_url,
    assert_query_parameter,
)

from auth_api.db import db
from auth_api.endpoints import AuthState
from auth_api.queries import LoginRecordQuery
from auth_api.config import (
    TOKEN_COOKIE_DOMAIN,
    OIDC_LOGIN_CALLBACK_PATH,
    OIDC_SSN_VALIDATE_CALLBACK_PATH,
)

from .bases import OidcCallbackEndpointsSubjectKnownBase


# -- Helpers -----------------------------------------------------------------


def assert_token(
        client: FlaskClient,
        opaque_token: str,
        expected_token: Dict[str, Any],
):
    """
    Provided an opaque token, this function translates it to an
    internal token and asserts on it's content.

    :param client:
    :param opaque_token:
    :param expected_token:
    :return:
    """
    client.set_cookie(
        server_name=TOKEN_COOKIE_DOMAIN,
        key=TOKEN_COOKIE_NAME,
        value=opaque_token,
        secure=True,
        httponly=True,
        samesite='Strict',
    )

    r_forwardauth = client.get('/token/forward-auth')

    r_inspect = client.get(
        path='/token/inspect',
        headers={TOKEN_HEADER_NAME: r_forwardauth.headers[TOKEN_HEADER_NAME]}
    )

    assert r_inspect.status_code == 200
    assert r_inspect.json == {'token': expected_token}


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture(params=[
    OIDC_LOGIN_CALLBACK_PATH,
    OIDC_SSN_VALIDATE_CALLBACK_PATH,
])
def callback_endpoint_path(request) -> str:
    """
    Returns path to callback endpoint.
    """
    return request.param


# -- Tests -------------------------------------------------------------------


class TestOidcCallbackEndpoints(object):
    """
    Common tests for all OIDC callback endpoints that require
    no setup or teardown.
    """

    @pytest.mark.unittest
    @pytest.mark.parametrize('state', [None, '', 'invalid-state'])
    def test__provide_invalid_state__should_return_status_400(
            self,
            client: FlaskClient,
            callback_endpoint_path: str,
            state: str,
    ):
        """
        If the Identity Provider omits state, or provides an invalid state,
        the endpoint should return HTTP status 400 Bad Request.

        :param client: API client
        :param callback_endpoint_path: Endpoint path
        :param state: Raw, encoded state
        """

        # -- Act -------------------------------------------------------------

        r = client.get(
            path=callback_endpoint_path,
            query_string={'state': state},
        )

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 400

    @pytest.mark.unittest
    @pytest.mark.parametrize('ip_error_description, error_code_expected', (
        # TODO Add all possible errors here:
        ('internal_error', 'E0'),
        ('internal_server_error', 'E0'),
        ('mitid_user_aborted', 'E1'),
    ))
    def test__provide_oidc_errors__should_redirect_to_return_url_with_internal_error_code(
            self,
            client: FlaskClient,
            state_encoder: TokenEncoder[AuthState],
            callback_endpoint_path: str,
            ip_error_description: str,
            error_code_expected: str,
    ):
        """
        If the Identity Provider provides an error, the endpoint should
        translate it into an internal error code, and 307-redirect the
        client back to the return_url defined in the state.

        :param client: API client
        :param state_encoder: AuthState encoder
        :param callback_endpoint_path: Endpoint path
        :param ip_error_description: Error description from Identity Provider
        :param error_code_expected: Expected (translated) output error code
        """

        # -- Arrange ---------------------------------------------------------

        state = AuthState(return_url='http://redirect-here.com/foobar')
        state_encoded = state_encoder.encode(state)

        # -- Act -------------------------------------------------------------

        r = client.get(
            path=callback_endpoint_path,
            query_string={
                'state': state_encoded,
                'error_description': ip_error_description,
            },
        )

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 307

        assert_base_url(
            url=r.headers['Location'],
            expected_base_url='http://redirect-here.com/foobar',
            check_path=True,
        )

        assert_query_parameter(
            url=r.headers['Location'],
            name='success',
            value='0',
        )

    @pytest.mark.unittest
    def test__fetch_token_fails__should_redirect_to_return_url_with_error_code(  # noqa: E501
            self,
            client: FlaskClient,
            mock_fetch_token: MagicMock,
            state_encoder: TokenEncoder[AuthState],
            callback_endpoint_path: str,
    ):
        """
        When failing to fetch token from Identity Provider, the endpoint
        should 307-redirect the client back to the return_url defined in
        the state with success=0 and error.

        :param client: API client
        :param mock_fetch_token: Mocked fetch_token() method @ OAuth2Session
        :param state_encoder: AuthState encoder
        :param callback_endpoint_path: Endpoint path
        """

        # -- Arrange ---------------------------------------------------------

        return_url = 'http://redirect-here.com/foobar'

        state = AuthState(return_url=return_url)
        state_encoded = state_encoder.encode(state)

        mock_fetch_token.side_effect = Exception('Test')

        # -- Act -------------------------------------------------------------

        r = client.get(
            path=callback_endpoint_path,
            query_string={'state': state_encoded},
        )

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 307

        assert_base_url(
            url=r.headers['Location'],
            expected_base_url=return_url,
            check_path=True,
        )

        assert_query_parameter(
            url=r.headers['Location'],
            name='success',
            value='0',
        )


class TestOidcCallbackEndpointsSubjectKnown(OidcCallbackEndpointsSubjectKnownBase):  # noqa: E501
    """
    Common tests for all OIDC callback endpoints where the Identity
    Provider's subject is known to the system. A setup-method creates
    the user before each test (look at the base-class for details).
    """

    @pytest.mark.integrationtest
    def test__should_307_redirect_to_correct_return_url(
            self,
            client: FlaskClient,
            callback_endpoint_path: str,
            return_url: str,
            state_encoded: str,
    ):
        """
        Redirect to client's return_url and add appropriate query parameters
        while keeping the original query parameters from return_url.

        :param client: API client
        :param return_url: Client's return_url
        :param state_encoded: AuthState, encoded
        """

        # -- Act -------------------------------------------------------------

        r = client.get(
            path=callback_endpoint_path,
            query_string={'state': state_encoded},
        )

        # -- Assert ----------------------------------------------------------

        redirect_location = r.headers['Location']

        assert r.status_code == 307

        # Redirect to Identity Provider should be to correct URL (without
        # taking query parameters into consideration)
        assert_base_url(
            url=redirect_location,
            expected_base_url=return_url,
            check_path=True,
        )

        # Redirect must include return_url's own query parameters
        assert_query_parameter(
            url=redirect_location,
            name='foo',
            value='bar',
        )

        # Redirect must include success=1
        assert_query_parameter(
            url=redirect_location,
            name='success',
            value='1',
        )

    @pytest.mark.integrationtest
    def test__should_create_token_in_database_and_set_cookie_correctly(
            self,
            client: FlaskClient,
            callback_endpoint_path: str,
            internal_subject: str,
            return_url: str,
            state_encoded: str,
            id_token: Dict[str, Any],
    ):
        """
        TODO

        :param client: API client
        :param return_url: Client's return_url
        :param state_encoded: AuthState, encoded
        """

        # -- Act -------------------------------------------------------------

        r = client.get(
            path=callback_endpoint_path,
            query_string={'state': state_encoded},
        )

        # -- Assert ----------------------------------------------------------

        cookies = CookieTester(r.headers) \
            .assert_has_cookies(TOKEN_COOKIE_NAME) \
            .assert_cookie(
                name=TOKEN_COOKIE_NAME,
                domain=TOKEN_COOKIE_DOMAIN,
                path='/',
                http_only=True,
                same_site=True,
                secure=True,
            )

        opaque_token = cookies.get_value(TOKEN_COOKIE_NAME)

        issued_expected = datetime \
            .fromtimestamp(id_token['iat']) \
            .astimezone(timezone.utc) \
            .isoformat()

        expires_expected = datetime \
            .fromtimestamp(id_token['exp']) \
            .astimezone(timezone.utc) \
            .isoformat()

        token_expected = {
            'issued': issued_expected,
            'expires': expires_expected,
            'actor': internal_subject,
            'subject': internal_subject,
            'scope': ['meteringpoints.read', 'measurements.read'],
        }

        assert_token(
            client=client,
            opaque_token=opaque_token,
            expected_token=token_expected,
        )

    @pytest.mark.integrationtest
    def test__should_register_user_login(
            self,
            client: FlaskClient,
            mock_session: db.Session,
            callback_endpoint_path: str,
            internal_subject: str,
            return_url: str,
            state_encoded: str,
    ):
        """
        Redirect to client's return_url and add appropriate query parameters
        while keeping the original query parameters from return_url.

        :param client: API client
        :param mock_session: Mocked database session
        :param internal_subject: Internal subject
        :param return_url: Client's return_url
        :param state_encoded: AuthState, encoded
        """

        # -- Act -------------------------------------------------------------

        client.get(
            path=callback_endpoint_path,
            query_string={'state': state_encoded},
        )

        # -- Assert ----------------------------------------------------------

        # Will raise an exception if not exactly one result was found
        LoginRecordQuery(mock_session) \
            .has_subject(internal_subject) \
            .one()

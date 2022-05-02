"""Tests specifically for OIDC logout endpoint."""

# Standard Library
from datetime import datetime, timedelta

# Third party
import pytest
import requests_mock
from flask.testing import FlaskClient

# First party
from origin.api.testing import CookieTester
from origin.auth import TOKEN_COOKIE_NAME
from origin.models.auth import InternalToken
from origin.tokens import TokenEncoder

# Local
from auth_api.config import (
    TOKEN_COOKIE_DOMAIN,
    TOKEN_COOKIE_HTTP_ONLY,
    TOKEN_COOKIE_PATH,
    INVALIDATE_PENDING_LOGIN_PATH,
    OIDC_API_LOGOUT_URL,
)
from auth_api.db import db
from auth_api.models import DbToken
from auth_api.queries import TokenQuery
from auth_api.state import AuthState


# -- Fixtures ----------------------------------------------------------------

@pytest.fixture(scope='function')
def an_url() -> str:
    """Return a dummy url."""
    return 'https://example.com'


@pytest.fixture(scope='function')
def oidc_adapter(request_mocker: requests_mock) -> requests_mock.Adapter:
    """Mock the oidc endpoint response to return status code 200."""

    adapter = request_mocker.post(
        OIDC_API_LOGOUT_URL,
        text='',
        status_code=200
    )
    return adapter


@pytest.fixture(scope='function')
def seeded_session(
        mock_session: db.Session,
        internal_token_encoded: InternalToken,
        id_token: str,
        subject: str,
        expires_datetime: datetime,
        issued_datetime: datetime,
        opaque_token: str,
) -> db.Session:
    """
    Seed the database with a token.

    This makes it seem like a user has been logged in.
    """

    mock_session.add(DbToken(
        subject=subject,
        opaque_token=opaque_token,
        internal_token=internal_token_encoded,
        issued=issued_datetime,
        expires=expires_datetime,
        id_token=id_token,
    ))

    mock_session.commit()
    return mock_session


# -- Tests -------------------------------------------------------------------


class TestOIDCEndpoint:
    """Tests the HTTP requests made to the oidcEndpoint."""

    @pytest.mark.integrationtest
    def test__logout__calling_oidc_logout_endpoint_with_correct_body(
            self,
            client: FlaskClient,
            seeded_session: db.Session,
            oidc_adapter: requests_mock.Adapter,
            internal_token_encoded: str,
            opaque_token: str,
            id_token: str,
    ):
        """
        Call OIDC endpoint with correct body on logout.

        When logging out, this is tests that the HTTP request payload
        sent to the OIDC logout endpoint, is actually correct.
        """

        # -- Arrange ---------------------------------------------------------

        # Create a cookie required for authentication
        client.set_cookie(
            server_name='domain.com',
            key=TOKEN_COOKIE_NAME,
            value=opaque_token,
        )

        # -- Act -------------------------------------------------------------

        client.post(
            path='/logout',
            headers={
                'Authorization': 'Bearer: ' + internal_token_encoded
            }
        )

        # -- Assert ----------------------------------------------------------

        assert oidc_adapter.call_count == 1

        # Make sure that the request payload
        # sent to the OIDC logout url is correct
        assert oidc_adapter.last_request.json() == {'id_token': id_token}

    @pytest.mark.integrationtest
    def test__logout_with_invalid_token__does_not_call_oidc(
            self,
            client: FlaskClient,
            seeded_session: db.Session,
            oidc_adapter: requests_mock.Adapter,
            internal_token_encoded: str,
            opaque_token: str,
    ):
        """
        Do not call OIDC when provided with invalid internal token.

        When logging out with invalid header, this is tests that no HTTP
        request is sent to the oidc endpoint.
        """

        # -- Arrange ---------------------------------------------------------

        # Create a cookie required for authentication
        client.set_cookie(
            server_name='domain.com',
            key=TOKEN_COOKIE_NAME,
            value='non-existent-opaque_token',
        )

        # -- Act -------------------------------------------------------------

        client.post(
            path='/logout',
            headers={
                'Authorization': 'Bearer: ' + internal_token_encoded
            }
        )

        # -- Assert ----------------------------------------------------------

        assert oidc_adapter.call_count == 0


class TestDatabaseTokens:
    """Test the token read/writes to the database."""

    @pytest.mark.integrationtest
    def test__logout_with_invalid_token__does_not_delete_any_session_tokens(
            self,
            client: FlaskClient,
            seeded_session: db.Session,
            internal_token_encoded: str,
            opaque_token: str,
    ):
        """
        Logout with invalid token does not delete any sessions tokens.

        When logging out with invalid header, this is tests that no HTTP
        request is sent to the oidc endpoint.
        """

        # -- Arrange ---------------------------------------------------------

        # Create a cookie required for authentication
        client.set_cookie(
            server_name='domain.com',
            key=TOKEN_COOKIE_NAME,
            value='non-existent-opaque_token',
        )

        # -- Act -------------------------------------------------------------

        client.post(
            path='/logout',
            headers={
                'Authorization': 'Bearer: ' + internal_token_encoded
            }
        )

        # -- Assert ----------------------------------------------------------

        query = TokenQuery(seeded_session) \
            .has_opaque_token(opaque_token)

        assert query.count() == 1

    @pytest.mark.integrationtest
    def test__logout_with_valid_token__does_delete_correct_session_tokens(
            self,
            client: FlaskClient,
            seeded_session: db.Session,
            oidc_adapter: requests_mock.Adapter,
            opaque_token: str,
            id_token: str,
            internal_token_encoded: str,
    ):
        """
        Delete the tokens from the database when user logs out.

        When logging out, this test that only the correct opaque_token
        is being deleted
        """

        # -- Arrange ---------------------------------------------------------

        # Add new token record in the database
        # that's not supposed to get deleted
        opaque_token_2 = 'opaque_token_test'

        seeded_session.add(DbToken(
            subject='subject',
            opaque_token=opaque_token_2,
            internal_token='internal_token_encoded',
            issued=datetime.now(),
            expires=datetime.now() + timedelta(days=1),
            id_token=id_token,
        ))

        seeded_session.commit()

        # Create a cookie required for authentication
        client.set_cookie(
            server_name='domain.com',
            key=TOKEN_COOKIE_NAME,
            value=opaque_token,
        )

        # -- Act -------------------------------------------------------------

        client.post(
            path='/logout',
            headers={
                'Authorization': 'Bearer: ' + internal_token_encoded
            }
        )

        # -- Assert ----------------------------------------------------------

        assert not TokenQuery(seeded_session) \
            .has_opaque_token(opaque_token) \
            .exists()

        assert TokenQuery(seeded_session) \
            .has_opaque_token(opaque_token_2) \
            .exists()


class TestHTTPResponse:
    """Tests the HTTP response returned by the endpoint."""

    def test__logout_success__returned_cookie_is_expired(
            self,
            client: FlaskClient,
            seeded_session: db.Session,
            oidc_adapter: requests_mock.Adapter,
            internal_token_encoded: str,
            opaque_token: str,
    ):
        """On logout success the returned cookie is expired."""

        # -- Arrange ---------------------------------------------------------

        # Create a cookie required for authentication
        client.set_cookie(
            server_name='domain.com',
            key=TOKEN_COOKIE_NAME,
            value=opaque_token,
        )

        # -- Act -------------------------------------------------------------

        response = client.post(
            path='/logout',
            headers={
                'Authorization': 'Bearer: ' + internal_token_encoded
            }
        )

        # -- Assert ----------------------------------------------------------

        cookies = CookieTester(response.headers) \
            .assert_has_cookies(TOKEN_COOKIE_NAME)

        # Get auth cookie
        auth_cookie = cookies.cookies[TOKEN_COOKIE_NAME]

        assert auth_cookie.value == ''
        assert auth_cookie['path'] == TOKEN_COOKIE_PATH
        assert auth_cookie['domain'] == TOKEN_COOKIE_DOMAIN
        assert auth_cookie['httponly'] == TOKEN_COOKIE_HTTP_ONLY
        assert auth_cookie['samesite'] == 'Strict'
        assert auth_cookie['secure'] is True

        # Get time when cookie expires
        expires_datatime = datetime.strptime(
            auth_cookie['expires'],
            "%a, %d %b %Y %H:%M:%S GMT",
        )

        # Assert that the expires_datetime has in fact expired
        assert expires_datatime < datetime.now()

    def test__logout_success__returned_correct_body(
            self,
            client: FlaskClient,
            seeded_session: db.Session,
            oidc_adapter: requests_mock.Adapter,
            internal_token_encoded: str,
            opaque_token: str,
    ):
        """When logging out, test that the response body is correct."""

        # -- Arrange ---------------------------------------------------------

        # Create a cookie required for authentication
        client.set_cookie(
            server_name='domain.com',
            key=TOKEN_COOKIE_NAME,
            value=opaque_token,
        )

        # -- Act -------------------------------------------------------------

        response = client.post(
            path='/logout',
            headers={
                'Authorization': 'Bearer: ' + internal_token_encoded
            }
        )

        # -- Assert ----------------------------------------------------------

        assert response.json == {'success': True}

    def test__invalidate_succeeds__returned_status_200(
        self,
        client: FlaskClient,
        id_token: str,
        an_url: str,
        state_encoder: TokenEncoder[AuthState],
        oidc_adapter: requests_mock.Adapter,
    ):
        """When invalidating a login, test that the response status is okay."""

        state = AuthState(
            fe_url=an_url,
            return_url=an_url,
            id_token=id_token,
        )

        state_encoded = state_encoder.encode(state)

        # -- Act -------------------------------------------------------------

        response = client.post(
            path=INVALIDATE_PENDING_LOGIN_PATH,
            json={
                'state': state_encoded,
            },
        )

        # -- Assert ----------------------------------------------------------

        assert oidc_adapter.call_count == 1

        assert response.status_code == 200

    def test__invalidate_fails_when_token_is_malformed__returned_error_status(
        self,
        client: FlaskClient,
        an_url: str,
        state_encoder: TokenEncoder[AuthState],
        oidc_adapter: requests_mock.Adapter,
    ):
        """
        Test with malformed AuthState.

        When invalidating with a malformed AuthState,
        test that the response status indicates an error.
        """

        state = AuthState(
            fe_url=an_url,
            return_url=an_url,
        )

        state_encoded = state_encoder.encode(state)

        # -- Act -------------------------------------------------------------

        response = client.post(
            path=INVALIDATE_PENDING_LOGIN_PATH,
            json={
                'state': state_encoded,
            },
        )

        # -- Assert ----------------------------------------------------------

        assert oidc_adapter.call_count == 0

        assert response.status_code == 400

    def test__invalidate_fails_when_token_is_missing__returned_error_status(
        self,
        client: FlaskClient,
        oidc_adapter: requests_mock.Adapter,
    ):
        """
        Test with malformed AuthState.

        When invalidating with a malformed AuthState,
        test that the response status indicates an error.
        """

        # -- Act -------------------------------------------------------------

        response = client.post(
            path=INVALIDATE_PENDING_LOGIN_PATH,
            json={},
        )

        # -- Assert ----------------------------------------------------------

        assert oidc_adapter.call_count == 0

        assert response.status_code == 400

import pytest
import requests_mock

from typing import Dict, Any
from unittest.mock import MagicMock
from flask.testing import FlaskClient

from origin.tokens import TokenEncoder
from origin.api.testing import (
    assert_base_url,
    assert_query_parameter,
)

from auth_api.db import db
from auth_api.state import AuthState


@pytest.fixture(scope='function')
def terms_url() -> str:
    """Path to terms."""
    return '/terms'


@pytest.fixture(scope='function')
def terms_accept_url() -> str:
    """Path to accepted terms."""
    return '/terms/accept'


class TestTermsAccept:
    """Tests cases where the user accepts the terms and conditions."""

    def test__user_accepts_terms__should_redirect_to_success(
        self,
        client: FlaskClient,
        mock_session: db.Session,
        datasync_adapter: requests_mock.Adapter,
        mock_get_jwk: MagicMock,
        mock_fetch_token: MagicMock,
        state_encoder: TokenEncoder[AuthState],
        jwk_public: str,
        ip_token: Dict[str, Any],
        token_tin: str,
        token_idp: str,
        token_subject: str,
        id_token_encrypted: str,
        terms_accept_url: str,
    ):
        """Tests if the user accepts terms and gets redirected with success."""
        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            tin=token_tin,
            id_token=id_token_encrypted,
            identity_provider=token_idp,
            external_subject=token_subject,
            terms_accepted=True,
            terms_version='0.1',
        )

        state_encoded = state_encoder.encode(state)
        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        res = client.post(
            path=terms_accept_url,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': True
            }
        )

        # -- Assert -----------------------------------------------------------

        assert res.status_code == 200

        assert_base_url(
            url=res.json['next_url'],
            expected_base_url=state.return_url,
            check_path=True,
        )

        assert_query_parameter(
            url=res.json['next_url'],
            name='success',
            value='1',
        )

    def test__user_accepts_terms__with_invalid_state__should_redirect_to_failure(  # noqa: E501
        self,
        client: FlaskClient,
        mock_session: db.Session,
        datasync_adapter: requests_mock.Adapter,
        mock_get_jwk: MagicMock,
        mock_fetch_token: MagicMock,
        state_encoder: TokenEncoder[AuthState],
        jwk_public: str,
        ip_token: Dict[str, Any],
        token_tin: str,
        terms_accept_url: str,
    ):
        """Tests if the users accepts terms and gets an invalid state."""

        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            tin=token_tin,
            id_token=ip_token['id_token'],
            terms_accepted=True,
            terms_version='0.1',
        )

        state_encoded = state_encoder.encode(state)
        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        res = client.post(
            path=terms_accept_url,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': True
            }
        )

        # -- Assert -----------------------------------------------------------

        assert res.status_code == 500

    def test__user_accepts_terms__should_redirect_with_httponly_cookie(
        self,
        client: FlaskClient,
        mock_session: db.Session,
        datasync_adapter: requests_mock.Adapter,
        mock_get_jwk: MagicMock,
        mock_fetch_token: MagicMock,
        state_encoder: TokenEncoder[AuthState],
        jwk_public: str,
        ip_token: Dict[str, Any],
        token_tin: str,
        token_idp: str,
        token_subject: str,
        id_token_encrypted: str,
        terms_accept_url: str,
    ):
        """Tests if the users accepts terms and gets a HttpOnly cookie."""
        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            tin=token_tin,
            id_token=id_token_encrypted,
            identity_provider=token_idp,
            external_subject=token_subject,
            terms_accepted=True,
            terms_version='0.1',
        )

        state_encoded = state_encoder.encode(state)
        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        res = client.post(
            path=terms_accept_url,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': True
            }
        )

        # -- Assert -----------------------------------------------------------

        assert res.status_code == 200

        cookie = res.headers['Set-Cookie']

        assert cookie is not None

        assert 'HttpOnly' in cookie


class TestTermsDecline:
    """Tests cases where the user declines the terms and conditions."""

    @pytest.mark.integrationtest
    def test__user_declines_terms__should_redirect_with_success_0(
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
        oidc_adapter: requests_mock.Adapter,
        terms_accept_url: str,
    ):
        """Tests if the user declines and redicect with success 0."""
        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            tin=token_tin,
            id_token=id_token_encrypted,
            identity_provider=token_idp,
            external_subject=token_subject,
            terms_accepted=False,
            terms_version='0.1',
        )

        state_encoded = state_encoder.encode(state)
        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        res = client.post(
            path=terms_accept_url,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': False
            }
        )

        # -- Assert -----------------------------------------------------------

        assert oidc_adapter.call_count == 1

        assert res.status_code == 200

        assert_base_url(
            url=res.json['next_url'],
            expected_base_url=state.return_url,
            check_path=True,
        )

        assert_query_parameter(
            url=res.json['next_url'],
            name='success',
            value='0',
        )


class TestTermsGet:
    """Tests whether terms get returns latest terms and success."""

    def test__user_gets_terms__should_return_latest_terms(
        self,
        client: FlaskClient,
        terms_url,
    ):
        """Tests whether terms get returns latest terms and success."""
        expected_head_line = 'Privacy Policy'
        expected_content = '<h1>Test file 2</h1>\n'
        expected_version = 'v2'

        res = client.get(
            path=terms_url
        )

        assert res.status_code == 200

        assert res.json['headline'] == expected_head_line

        assert res.json['terms'] == expected_content

        assert res.json['version'] == expected_version

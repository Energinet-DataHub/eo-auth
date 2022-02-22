import pytest

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
from auth_api.config import TERMS_ACCEPT_PATH, TERMS_PATH


class TestTermsAccept:
    """
    Tests cases where the user accepts the terms and conditions
    """

    def test__user_accepts_terms__should_redirect_to_success(
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

        r = client.post(
            path=TERMS_ACCEPT_PATH,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': True
            }
        )

        # -- Assert -----------------------------------------------------------

        assert r.status_code == 200

        assert_base_url(
            url=r.json['next_url'],
            expected_base_url=state.return_url,
            check_path=True,
        )

        assert_query_parameter(
            url=r.json['next_url'],
            name='success',
            value='1',
        )

    def test__user_accepts_terms__with_invalid_state__should_redirect_to_failure(  # noqa: E501
        self,
        client: FlaskClient,
        mock_session: db.Session,
        mock_get_jwk: MagicMock,
        mock_fetch_token: MagicMock,
        state_encoder: TokenEncoder[AuthState],
        jwk_public: str,
        ip_token: Dict[str, Any],
        token_tin: str,
    ):
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

        r = client.post(
            path=TERMS_ACCEPT_PATH,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': True
            }
        )

        # -- Assert -----------------------------------------------------------

        assert r.status_code == 500

    def test__user_accepts_terms__should_redirect_with_httponly_cookie(
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

        r = client.post(
            path=TERMS_ACCEPT_PATH,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': True
            }
        )

        # -- Assert -----------------------------------------------------------

        assert r.status_code == 200

        cookie = r.headers['Set-Cookie']

        assert cookie is not None

        assert 'HttpOnly' in cookie


class TestTermsDecline:
    """
    Tests cases where the user declines the terms and conditions.
    """

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
    ):
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

        r = client.post(
            path=TERMS_ACCEPT_PATH,
            json={
                'state': state_encoded,
                'version': '0.1',
                'accepted': False
            }
        )

        # -- Assert -----------------------------------------------------------

        assert r.status_code == 200

        assert_base_url(
            url=r.json['next_url'],
            expected_base_url=state.return_url,
            check_path=True,
        )

        assert_query_parameter(
            url=r.json['next_url'],
            name='success',
            value='0',
        )


class TestTermsGet:
    """
    Tests whether terms get returns latest terms and success
    """

    def test__user_gets_terms__should_return_latest_terms(
        self,
        client: FlaskClient,
    ):
        expectedHeadline = 'Privacy Policy'
        expectedContent = '<h1>Test file 2</h1>\n'
        expectedVersion = 'v2'

        r = client.get(
            path=TERMS_PATH
        )

        assert r.status_code == 200

        assert r.json['headline'] == expectedHeadline

        assert r.json['terms'] == expectedContent

        assert r.json['version'] == expectedVersion

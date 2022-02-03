from datetime import datetime
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
from auth_api.endpoints import AuthState
from auth_api.config import TERMS_ACCEPT_PATH, CREATE_USER_URL


class TestTermsAccept:
    """
    Tests cases where the user accepts the terms and conditions
    """

    @pytest.mark.integrationtest
    def test__user_accepts_terms__should_redirect_to_next_url(
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

        assert r.status_code == 200

        # Redirect to terms should be to correct URL (without
        # taking query parameters into consideration)
        assert_base_url(
            url=r.json['next_url'],
            expected_base_url=CREATE_USER_URL,
            check_path=True,
        )

        # Redirect to terms must have correct query params

        assert_query_parameter(
            url=r.json['next_url'],
            name='state',
            value=state_encoded
        )


class TestTermsDecline:
    """
    Tests cases where the user declines the terms and conditions.
    """

    @pytest.mark.integrationtest
    def test__user_accepts_terms__should_redirect_to_next_url(
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

        # Redirect to terms should be to correct URL (without
        # taking query parameters into consideration)
        assert_base_url(
            url=r.json['next_url'],
            expected_base_url='https://redirect-here.com/foobar',
            check_path=True,
        )

        # Redirect to terms must have correct query params

        assert_query_parameter(
            url=r.json['next_url'],
            name='success',
            value='0',
        )

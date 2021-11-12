import pytest
from uuid import uuid4
from typing import Dict, Any
from unittest.mock import MagicMock

from energytt_platform.tokens import TokenEncoder

from auth_api.db import db
from auth_api.endpoints import AuthState
from auth_api.models import DbUser, DbExternalUser


class OidcCallbackEndpointsSubjectKnownBase:
    """
    Base class for all OIDC callback endpoints that tests behavior, where
    the Identity Provider's subject is known to the system. A setup-method
    creates the user before each test.
    """

    @pytest.fixture(scope='function')
    def internal_subject(self) -> str:
        """
        Our internal subject
        """
        return str(uuid4())

    @pytest.fixture(scope='function')
    def return_url(self) -> str:
        """
        Client's return_url
        """
        return 'http://redirect-here.com/foobar?foo=bar'

    @pytest.fixture(scope='function')
    def state_encoded(
            self,
            state_encoder: TokenEncoder[AuthState],
            return_url: str,
    ) -> str:
        """
        AuthState, encoded
        """
        state = AuthState(return_url=return_url)
        state_encoded = state_encoder.encode(state)
        return state_encoded

    @pytest.fixture(scope='function', autouse=True)
    def setup(
            self,
            mock_session: db.Session,
            mock_get_jwk: MagicMock,
            mock_fetch_token: MagicMock,
            jwk_public: str,
            ip_token: Dict[str, Any],
            token_subject: str,
            token_idp: str,
            token_ssn: str,
            internal_subject: str,
    ) -> db.Session:
        """
        Inserts a mock-user into the database.
        """

        # -- OAuth2Session object methods ------------------------------------

        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Insert user into database ---------------------------------------

        mock_session.begin()

        mock_session.add(DbUser(
            subject=internal_subject,
            ssn=token_ssn,
        ))

        mock_session.add(DbExternalUser(
            subject=internal_subject,
            identity_provider=token_idp,
            external_subject=token_subject,
        ))

        mock_session.commit()

        return mock_session

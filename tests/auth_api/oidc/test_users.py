from uuid import uuid4
import pytest

from typing import Dict, Any
from unittest.mock import MagicMock
from flask.testing import FlaskClient

from origin.tokens import TokenEncoder

from auth_api.db import db
from auth_api.endpoints import AuthState
from auth_api.config import CREATE_USER_PATH
from auth_api.models import DbExternalUser, DbUser
from auth_api.queries import UserQuery


# -- Tests --------------------------------------------------------------------

class TestCreateUser:

    # -- Fixtures -------------------------------------------------------------
    """
    Tests cases when a new user is created
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
        return 'https://redirect-here.com/foobar?foo=bar'

    @pytest.fixture(scope='function')
    def fe_url(self) -> str:
        """
        Client's fe_url
        """
        return 'https://foobar.com/'

    @pytest.fixture(scope='function')
    def seeded_session(
            self,
            mock_session: db.Session,
            mock_get_jwk: MagicMock,
            mock_fetch_token: MagicMock,
            jwk_public: str,
            ip_token: Dict[str, Any],
            token_subject: str,
            token_idp: str,
            token_tin: str,
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
            cvr=token_tin,
        ))

        mock_session.add(DbExternalUser(
            subject=internal_subject,
            identity_provider=token_idp,
            external_subject=token_subject,
        ))

        mock_session.commit()

        return mock_session

    @pytest.mark.integrationtest
    def test__create_user__if_user_does_not_exist__it_should_insert_a_user(
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
    ):
        # -- Arrange ----------------------------------------------------------

        state = AuthState(
            fe_url='https://foobar.com',
            return_url='https://redirect-here.com/foobar',
            tin=token_tin,
            id_token=ip_token['id_token'],
            terms_accepted=True,
            terms_version='0.1',
            identity_provider=token_idp,
            external_subject=token_subject,
        )

        state_encoded = state_encoder.encode(state)
        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        client.post(
            path=CREATE_USER_PATH,
            json={
                'state': state_encoded,
            }
        )

        # -- Assert -----------------------------------------------------------

        assert UserQuery(mock_session) \
            .has_tin(token_tin) \
            .count() == 1

    @pytest.mark.integrationtest
    def test__create_user__when_a_user_already_exists__it_should_not_insert_a_user(  # noqa: E501
        self,
        client: FlaskClient,
        seeded_session: db.Session,
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

        client.post(
            path=CREATE_USER_PATH,
            json={
                'state': state_encoded,
            }
        )

        # -- Assert -----------------------------------------------------------

        assert UserQuery(seeded_session) \
            .has_tin(token_tin) \
            .count() == 1

    @pytest.mark.integrationtest
    @pytest.mark.parametrize('state', [None, '', 'invalid-state'])
    def test__create_user__when_it_cannot_decode_state__it_should_not_insert_a_user(  # noqa: E501
        self,
        client: FlaskClient,
        mock_session: db.Session,
        mock_get_jwk: MagicMock,
        mock_fetch_token: MagicMock,
        jwk_public: str,
        ip_token: Dict[str, Any],
        token_tin: str,
        state: str,
    ):
        # -- Arrange ----------------------------------------------------------

        mock_get_jwk.return_value = jwk_public
        mock_fetch_token.return_value = ip_token

        # -- Act --------------------------------------------------------------

        client.post(
            path=CREATE_USER_PATH,
            json={
                'state': state,
            }
        )

        # -- Assert -----------------------------------------------------------

        assert UserQuery(mock_session) \
            .has_tin(token_tin) \
            .count() == 0

    @pytest.mark.integrationtest
    def test__create_user__when_terms_have_not_been_accepted__it_should_not_insert_a_user(  # noqa: E501
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

        client.post(
            path=CREATE_USER_PATH,
            json={
                'state': state_encoded,
            }
        )

        # -- Assert -----------------------------------------------------------

        assert UserQuery(mock_session) \
            .has_tin(token_tin) \
            .count() == 0

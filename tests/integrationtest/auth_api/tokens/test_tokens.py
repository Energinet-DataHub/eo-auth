import pytest
from energytt_platform.auth import TOKEN_COOKIE_NAME
from flask.testing import FlaskClient
from datetime import datetime, timedelta, timezone

from energytt_platform.sql import SqlEngine

from auth_api.models import DbToken


class TestForwardAuth:
    """
    TODO
    """

    def test__no_token__should_return_no_header_and_status_401(
            self,
            client: FlaskClient,
            mock_session: SqlEngine.Session,
    ):
        """
        TODO
        """

        # -- Act -------------------------------------------------------------

        r = client.get('/token/forward-auth')

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 401
        assert 'Authorization' not in r.headers

    def test__invalid_token__should_return_no_header_and_status_401(
            self,
            client: FlaskClient,
            mock_session: SqlEngine.Session,
    ):
        """
        TODO
        """

        # -- Act -------------------------------------------------------------

        client.set_cookie(
            server_name='domain.com',  # TODO
            key=TOKEN_COOKIE_NAME,
            value='INVALID-TOKEN',
        )

        r = client.get('/token/forward-auth')

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 401
        assert 'Authorization' not in r.headers

    @pytest.mark.parametrize('issued, expires', [
        # Token is issued AFTER now:
        (
            datetime.now(tz=timezone.utc) + timedelta(days=1),
            datetime.now(tz=timezone.utc) + timedelta(days=2),
        ),
        # Token is expired:
        (
            datetime.now(tz=timezone.utc) - timedelta(days=2),
            datetime.now(tz=timezone.utc) - timedelta(days=1),
        ),
    ])
    def test__token_issue_or_expire_not_valid_right_now__should_return_no_header_and_status_401(
            self,
            issued: datetime,
            expires: datetime,
            client: FlaskClient,
            mock_session: SqlEngine.Session,
    ):
        """
        TODO
        """

        opaque_token = '12345'
        internal_token = '54321'

        mock_session.begin()
        mock_session.add(DbToken(
            opaque_token=opaque_token,
            internal_token=internal_token,
            id_token='',  # Irrelevant
            issued=issued,
            expires=expires,
            subject='subject',
        ))
        mock_session.commit()

        # -- Act -------------------------------------------------------------

        client.set_cookie(
            server_name='domain.com',  # TODO
            key=TOKEN_COOKIE_NAME,
            value=opaque_token,
        )

        r = client.get('/token/forward-auth')

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 401
        assert 'Authorization' not in r.headers

    def test__token_exists__should_return_authorization_header_and_status_200(
            self,
            client: FlaskClient,
            mock_session: SqlEngine.Session,
    ):
        """
        TODO
        """

        opaque_token = '12345'
        internal_token = '54321'

        mock_session.begin()
        mock_session.add(DbToken(
            opaque_token=opaque_token,
            internal_token=internal_token,
            id_token='',  # Irrelevant
            issued=datetime.now(tz=timezone.utc),
            expires=datetime.now(tz=timezone.utc) + timedelta(days=1),
            subject='subject',
        ))
        mock_session.commit()

        # -- Act -------------------------------------------------------------

        client.set_cookie(
            server_name='domain.com',  # TODO
            key=TOKEN_COOKIE_NAME,
            value=opaque_token,
        )

        r = client.get('/token/forward-auth')

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 200
        assert r.headers['Authorization'] == f'Bearer: {internal_token}'

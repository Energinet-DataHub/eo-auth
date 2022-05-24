"""Tests user information."""
import pytest
from flask.testing import FlaskClient
from auth_api.db import db
from auth_api.models import DbCompany, DbUser, DbToken
from datetime import datetime

# # -- fixtures ---------------------------------------------------------------


@pytest.fixture(scope='function')
def seeded_session(
    mock_session: db.Session,
    internal_token_encoded: str,
    id_token: str,
    subject: str,
    actor: str,
    expires_datetime: datetime,
    issued_datetime: datetime,
    opaque_token: str,
    ssn: str,
) -> db.Session:
    """Mock database with a list of mock-users and mock-external-users."""

    # -- Insert user into database ---------------------------------------

    mock_session.begin()

    user = DbUser(
        subject=actor,
        ssn=ssn,
    )

    mock_session.add(user)

    mock_session.add(DbCompany(
        id=subject,
        tin="tin_1",
        users=[user],
    ))

    # -- Insert Token into database ---------------------------------------

    mock_session.add(DbToken(
        subject=subject,
        opaque_token=opaque_token,
        internal_token=internal_token_encoded,
        issued=issued_datetime,
        expires=expires_datetime,
        id_token=id_token,
    ))

    mock_session.commit()

    yield mock_session


class TestUserInformation(object):
    """Test user information."""

    def test__user_info__returns_unauthorized_without_authorization(
            self,
            client: FlaskClient,
    ):
        """When no token provided return 401."""

        # -- Act -------------------------------------------------------------

        res = client.get('/user/info')

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 401

    def test__user_info__returns_unauthorized_without_a_valid_authorization(
            self,
            client: FlaskClient,
    ):
        """When invalid token provided return 401."""

        # -- Act -------------------------------------------------------------

        res = client.get('/user/info', headers={'Authorization': 'not valid'})

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 401

    def test__user_info__returns_info_with_correct_request(
            self,
            client: FlaskClient,
            internal_token_encoded: str,
            seeded_session: db.Session,
    ):
        """When proper token provided return user info."""

        # -- Act -------------------------------------------------------------

        res = client.get('/user/info', headers={'Authorization': 'Bearer: ' + internal_token_encoded})  # noqa E501

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 200

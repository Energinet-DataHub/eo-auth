"""Tests user information."""
import pytest
from flask.testing import FlaskClient
from auth_api.db import db
from auth_api.models import DbUser, DbToken
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Dict, Any
from origin.models.auth import InternalToken
from origin.tokens import TokenEncoder
from authlib.jose import jwt

# # -- fixtures ---------------------------------------------------------------


@pytest.fixture(scope='function')
def subject() -> str:
    """Return the subject."""

    return 'subject'


@pytest.fixture(scope='function')
def actor() -> str:
    """Return an actor name."""

    return 'actor'


@pytest.fixture(scope='function')
def opaque_token() -> str:
    """
    Return Opaque token.

    Return a opaque token, which are the token
    that are actual visible to the frontend.
    """

    return str(uuid4())


@pytest.fixture(scope='function')
def issued_datetime() -> datetime:
    """Datetime that indicates when a token has been issued."""

    return datetime.now(tz=timezone.utc)


@pytest.fixture(scope='function')
def expires_datetime() -> datetime:
    """Datetime that indicates when a token will expire."""

    return datetime.now(tz=timezone.utc) + timedelta(days=1)


@pytest.fixture(scope='function')
def userinfo_token_encoded(
        jwk_private: str,
        userinfo_token: Dict[str, Any],
) -> str:
    """Mock userinfo-token from Identity Provider (encoded)."""

    token = jwt.encode(
        header={'alg': 'RS256'},
        payload=userinfo_token,
        key=jwk_private,
    )

    return token.decode()


@pytest.fixture(scope='function')
def internal_token(
    subject: str,
    expires_datetime: datetime,
    issued_datetime: datetime,
    actor: str,
) -> InternalToken:
    """Return the internal token used within the system itself."""

    return InternalToken(
        issued=issued_datetime,
        expires=expires_datetime,
        actor=actor,
        subject=subject,
        scope=['scope1', 'scope2'],
    )


@pytest.fixture(scope='function')
def internal_token_encoded(
    internal_token: InternalToken,
    internal_token_encoder: TokenEncoder[InternalToken],
) -> str:
    """Return the internal token in encoded string format."""

    return internal_token_encoder \
        .encode(internal_token)


@pytest.fixture(scope='function')
def id_token() -> str:
    """Return a dummy identity provider id_token."""

    return 'id-token'


@pytest.fixture(scope='function')
def ssn() -> str:
    """Return a dummy identity provider id_token."""

    return '123456789'


@pytest.fixture(scope='function')
def tin() -> str:
    """Return a dummy identity provider id_token."""

    return '987654321'


@pytest.fixture(scope='function')
def seeded_session(
    mock_session: db.Session,
    internal_token_encoded: str,
    id_token: str,
    subject: str,
    expires_datetime: datetime,
    issued_datetime: datetime,
    opaque_token: str,
    ssn: str,
    tin: str,
) -> db.Session:
    """Mock database with a list of mock-users and mock-external-users."""

    # -- Insert user into database ---------------------------------------

    mock_session.begin()

    mock_session.add(DbUser(
        subject=subject,
        ssn=ssn,
        tin=tin,
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

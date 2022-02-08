from uuid import uuid4

import pytest
from origin.tokens import TokenEncoder
from origin.models.auth import InternalToken

from auth_api.db import db
from auth_api.models import DbUser, DbExternalUser, DbLoginRecord, DbToken
from datetime import datetime, timezone, timedelta

# -- Fixtures ----------------------------------------------------------------

DB_USER_1 = {
    "subject": 'SUBJECT_1',
    "ssn": "SSN_1",
    "cvr": 'CVR_1'
}

DB_USER_2 = {
    "subject": 'SUBJECT_2',
    "ssn": "SSN_2",
    "cvr": 'CVR_2'
}

DB_USER_3 = {
    "subject": 'SUBJECT_3',
    "ssn": "SSN_3",
    "cvr": 'CVR_3'
}

EXTERNAL_USER_4 = {
    "subject": 'SUBJECT_1',
    "identity_provider": "mitid",
    "external_subject": 'SUBJECT_4'
}

EXTERNAL_USER_5 = {
    "subject": 'SUBJECT_1',
    "identity_provider": "nemid",
    "external_subject": 'SUBJECT_5'
}

EXTERNAL_USER_6 = {
    "subject": 'SUBJECT_3',
    "identity_provider": "nemid",
    "external_subject": 'SUBJECT_6'
}

LOGIN_RECORD_USER_7 = {
    "subject": 'SUBJECT_LOGIN_RECORD',
    "created": datetime.now(tz=timezone.utc)
}

USER_LIST = [
    DB_USER_1,
    DB_USER_2,
    DB_USER_3,
]

USER_EXTERNAL_LIST = [
    EXTERNAL_USER_4,
    EXTERNAL_USER_5,
    EXTERNAL_USER_6,
]

USER_LOGIN_RECORD = [
    LOGIN_RECORD_USER_7
]


class TestQueryBase:
    """
    Base class for all queries that tests behavior, where
    the the user's token in known by the system.
    This setup's all the required users before each test.
    """
    @pytest.fixture(scope='function')
    def id_token(self) -> str:
        """
        Returns a dummy idtoken used for the OpenID Connect
        identity provider.
        """
        return 'id-token'

    @pytest.fixture(scope='function')
    def subject(self) -> str:
        """
        Returns the subject.
        """
        return 'subject'

    @pytest.fixture(scope='function')
    def actor(self) -> str:
        """
        Returns an actor name.
        """
        return 'actor'

    @pytest.fixture(scope='function')
    def opaque_token(self) -> str:
        """
        Returns a opaque token, which are the token
        that are actual visible to the frontend.
        """
        return str(uuid4())

    @pytest.fixture(scope='function')
    def issued_datetime(self) -> datetime:
        """
        A datetime that indicates when a token has been issued
        """
        return datetime.now(tz=timezone.utc)

    @pytest.fixture(scope='function')
    def expires_datetime(self) -> datetime:
        """
        A datetime that indicates when a token will expire
        """
        return datetime.now(tz=timezone.utc) + timedelta(days=1)

    @pytest.fixture(scope='function')
    def internal_token(
        self,
        subject: str,
        expires_datetime: datetime,
        issued_datetime: datetime,
        actor: str,
    ) -> InternalToken:
        """
        Returns the internal token used within the system itself.
        """
        return InternalToken(
            issued=issued_datetime,
            expires=expires_datetime,
            actor=actor,
            subject=subject,
            scope=['scope1', 'scope2'],
        )

    @pytest.fixture(scope='function')
    def internal_token_encoded(
        self,
        internal_token: InternalToken,
        internal_token_encoder: TokenEncoder[InternalToken],
    ) -> str:
        """
        Returns the internal token in encoded string format.
        """
        return internal_token_encoder \
            .encode(internal_token)

    @pytest.fixture(scope='function')
    def seeded_session(
        self,
        mock_session: db.Session,
        internal_token_encoded: str,
        id_token: str,
        subject: str,
        expires_datetime: datetime,
        issued_datetime: datetime,
        opaque_token: str,
        internal_token: InternalToken,
    ) -> db.Session:
        """
        Inserts a list of mock-users and mock-external-users into the database.
        """

        # -- Insert user into database ---------------------------------------

        mock_session.begin()

        for user in USER_LIST:
            mock_session.add(DbUser(
                subject=user['subject'],
                ssn=user['ssn'],
                cvr=user['cvr'],
            ))

        for user in USER_EXTERNAL_LIST:
            mock_session.add(DbExternalUser(
                subject=user['subject'],
                identity_provider=user['identity_provider'],
                external_subject=user['external_subject'],
            ))

        for user in USER_LOGIN_RECORD:
            mock_session.add(DbLoginRecord(
                subject=user['subject'],
                created=user['created'],
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

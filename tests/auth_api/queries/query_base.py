
import pytest
from origin.models.auth import InternalToken

from auth_api.db import db
from auth_api.models import DbUser, DbExternalUser, DbLoginRecord, DbToken
from datetime import datetime, timezone

# -- Fixtures ----------------------------------------------------------------

DB_USER_1 = {
    "subject": 'SUBJECT_1',
    "ssn": "SSN_1",
    "tin": 'TIN_1'
}

DB_USER_2 = {
    "subject": 'SUBJECT_2',
    "ssn": "SSN_2",
    "tin": 'TIN_2'
}

DB_USER_3 = {
    "subject": 'SUBJECT_3',
    "ssn": "SSN_3",
    "tin": 'TIN_3'
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
    Base class for all test queries.

    Base class for all queries that tests behavior, where
    the the user's token in known by the system.
    This setup's all the required users before each test.
    """

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
        """Mock database with a list of mock-users and mock-external-users."""

        # -- Insert user into database ---------------------------------------

        mock_session.begin()

        for user in USER_LIST:
            mock_session.add(DbUser(
                subject=user['subject'],
                ssn=user['ssn'],
                tin=user['tin'],
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

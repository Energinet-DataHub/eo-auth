from uuid import uuid4

import pytest
from origin.tokens import TokenEncoder
from origin.models.auth import InternalToken

from auth_api.db import db
from auth_api.models import (
    DbCompany,
    DbUser,
    DbExternalUser,
    DbLoginRecord,
    DbToken
)
from datetime import datetime, timezone, timedelta

# -- Fixtures ----------------------------------------------------------------

DB_USER_1 = {
    "subject": 'SUBJECT_1',
    "ssn": "SSN_1",
    "companies": [],
}

DB_USER_2 = {
    "subject": 'SUBJECT_2',
    "ssn": "SSN_2",
    "companies": [],
}

DB_USER_3 = {
    "subject": 'SUBJECT_3',
    "ssn": "SSN_3",
    "companies": [],
}

DB_COMPANY_1 = {
    "id": "COMPANY_1",
    "tin": "TIN_1",
    "users": [DB_USER_1],
}

DB_COMPANY_2 = {
    "id": "COMPANY_2",
    "tin": "TIN_2",
    "users": [DB_USER_2],
}

DB_COMPANY_3 = {
    "id": "COMPANY_3",
    "tin": "TIN_3",
    "users": [DB_USER_3],
}

# Update the user objects to be part of the companies as well
DB_USER_1['companies'] = [DB_COMPANY_1]
DB_USER_2['companies'] = [DB_COMPANY_2]
DB_USER_3['companies'] = [DB_COMPANY_3]

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

COMPANY_LIST = [
    DB_COMPANY_1,
    DB_COMPANY_2,
    DB_COMPANY_3,
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
    def id_token(self) -> str:
        """Return dummy token used for the OpenID Connect identity provider."""

        return 'id-token'

    @pytest.fixture(scope='function')
    def subject(self) -> str:
        """Return the subject."""

        return 'subject'

    @pytest.fixture(scope='function')
    def actor(self) -> str:
        """Return an actor name."""

        return 'actor'

    @pytest.fixture(scope='function')
    def opaque_token(self) -> str:
        """
        Return Opaque token.

        Return a opaque token, which are the token
        that are actual visible to the frontend.
        """

        return str(uuid4())

    @pytest.fixture(scope='function')
    def issued_datetime(self) -> datetime:
        """Datetime that indicates when a token has been issued."""

        return datetime.now(tz=timezone.utc)

    @pytest.fixture(scope='function')
    def expires_datetime(self) -> datetime:
        """Datetime that indicates when a token will expire."""

        return datetime.now(tz=timezone.utc) + timedelta(days=1)

    @pytest.fixture(scope='function')
    def internal_token(
        self,
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
        self,
        internal_token: InternalToken,
        internal_token_encoder: TokenEncoder[InternalToken],
    ) -> str:
        """Return the internal token in encoded string format."""

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
        """Mock database with a list of mock-users and mock-external-users."""

        # -- Insert user into database ---------------------------------------

        db_users = {
            user['subject']: DbUser(
                subject=user['subject'],
                ssn=user['ssn'],
            )
            for user in USER_LIST
        }

        for db_user in db_users.values():
            mock_session.add(db_user)

        # -- Insert companies into database ----------------------------------

        db_companies = {
            company['id']: DbCompany(
                id=company['id'],
                tin=company['tin'],
                # Find correct users and add them too
                users=[db_users[user['subject']] for user in company['users']]
            )
            for company in COMPANY_LIST
        }

        for db_company in db_companies.values():
            mock_session.add(db_company)

        # -- Insert external users into database ------------------------------

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

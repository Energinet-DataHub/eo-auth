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

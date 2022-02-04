import pytest

from auth_api.db import db
from auth_api.queries import LoginRecordQuery
from .query_base import TestQueryBase, USER_LOGIN_RECORD


class TestLoginRecordQuery(TestQueryBase):
    """
    Tests cases where a subject in written into the database
    and can be returned if correct subject is called.
    """
    @pytest.mark.parametrize('user', USER_LOGIN_RECORD)
    def test__has_subject__subject_exits__return_correct_subject(
            self,
            seeded_session: db.Session,
            user,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        :param user: list of users
        """

        # -- Act -------------------------------------------------------------

        query = LoginRecordQuery(seeded_session)
        fetched_user = query.has_subject('SUBJECT_LOGIN_RECORD').one_or_none()

        # -- Assert ----------------------------------------------------------
        assert fetched_user is not None
        assert fetched_user.subject == user['subject']

    def test__has_subject__subject_does_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        """
        # -- Act -------------------------------------------------------------

        query = LoginRecordQuery(seeded_session)
        fetched_user = query.has_subject('INVALID_SUBJECT_LOGIN_RECORD').one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_user is None



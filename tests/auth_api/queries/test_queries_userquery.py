import pytest

from auth_api.db import db
from auth_api.queries import UserQuery
from tests.auth_api.queries.query_base import TestQueryBase, USER_LIST


class TestUserQueries(TestQueryBase):
    """
    Test
    """
    @pytest.mark.parametrize('user', USER_LIST)
    def test__has_ssn__ssn_exists__return_correct_user(
        self,
        seeded_session: db.Session,
        user: dict,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        :param user: Current user inserted into the test
        """

        # -- Act -------------------------------------------------------------

        query = UserQuery(seeded_session)
        fetched_user_ssn = query.has_ssn(user['ssn']).one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_user_ssn is not None
        assert fetched_user_ssn.ssn == user['ssn']


    def test__has_snn__ssn_does_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        """
        # -- Act -------------------------------------------------------------

        query = UserQuery(seeded_session)
        fetched_user = query.has_ssn('invalid_ssn').one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_user is None

    @pytest.mark.parametrize('user', USER_LIST)
    def test__has_tin__tin_exists__return_correct_user(
        self,
        seeded_session: db.Session,
        user: dict,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        :param user: Current user inserted into the test
        """
        # -- Act -------------------------------------------------------------

        query = UserQuery(seeded_session)
        fetched_user_tin = query.has_tin(user['cvr']).one_or_none()

        # -- Assert ----------------------------------------------------------
        assert fetched_user_tin is not None
        assert fetched_user_tin.cvr == user['cvr']

    def test__has_tin__tin_does_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        """
        # -- Act -------------------------------------------------------------

        query = UserQuery(seeded_session)
        fetched_user = query.has_tin('invalid_tin').one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_user is None

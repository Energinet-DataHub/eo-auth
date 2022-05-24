import pytest

from auth_api.db import db
from auth_api.queries import UserQuery
from tests.auth_api.queries.query_base import TestQueryBase, USER_LIST


class TestUserQueries(TestQueryBase):
    """Test user queries."""

    @pytest.mark.parametrize('user', USER_LIST)
    def test__has_ssn__ssn_exists__return_correct_user(
        self,
        seeded_session: db.Session,
        user: dict,
    ):
        """
        If user with SSN exists return correct user.

        :param seeded_session: Mocked database session
        :param user: Current user inserted into the test
        """

        # -- Act -------------------------------------------------------------

        query = UserQuery(seeded_session) \
            .has_ssn(user['ssn']) \
            .one_or_none()

        # -- Assert ----------------------------------------------------------

        assert query is not None
        assert query.ssn == user['ssn']

    def test__has_snn__ssn_does_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
        """
        When searching for non existent SSN, return None.

        :param seeded_session: Mocked database session
        """

        # -- Act -------------------------------------------------------------

        query = UserQuery(seeded_session) \
            .has_ssn('invalid_ssn') \
            .one_or_none()

        # -- Assert ----------------------------------------------------------

        assert query is None

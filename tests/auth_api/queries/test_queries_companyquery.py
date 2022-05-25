import pytest

from auth_api.db import db
from auth_api.models import DbCompany
from auth_api.queries import CompanyQuery
from tests.auth_api.queries.query_base import (
    COMPANY_LIST,
    TestQueryBase,
)


class TestCompanyQueries(TestQueryBase):
    """Test user queries."""

    @pytest.mark.parametrize('company', COMPANY_LIST)
    def test__has_id__id_exists__return_correct_company(
        self,
        seeded_session: db.Session,
        company: dict,
    ):
        """
        If company with id exists return correct company.

        :param seeded_session: Mocked database session
        :param company: Current company inserted into the test
        """

        # -- Act -------------------------------------------------------------

        fetched_company: DbCompany = CompanyQuery(seeded_session) \
            .has_id(company['id']) \
            .one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_company is not None
        assert fetched_company.id == company['id']

    def test__has_id__id_does_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
        """
        If company with id does not exist return none.

        :param seeded_session: Mocked database session
        """

        # -- Act -------------------------------------------------------------

        fetched_company: DbCompany = CompanyQuery(seeded_session) \
            .has_id("THIS_ID_DOES_NOT_EXIST") \
            .one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_company is None

    @pytest.mark.parametrize('company', COMPANY_LIST)
    def test__has_tin__tin_exists__return_correct_company(
        self,
        seeded_session: db.Session,
        company: dict,
    ):
        """
        If company with tin exists return correct company.

        :param seeded_session: Mocked database session
        :param company: Current company inserted into the test
        """

        # -- Act -------------------------------------------------------------

        fetched_company: DbCompany = CompanyQuery(seeded_session) \
            .has_tin(company['tin']) \
            .one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_company is not None
        assert fetched_company.tin == company['tin']
        assert fetched_company.id == company['id']

    def test__has_tin__tin_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
        """
        If company with tin that does not exists return none.

        :param seeded_session: Mocked database session
        """

        # -- Act -------------------------------------------------------------

        fetched_company: DbCompany = CompanyQuery(seeded_session) \
            .has_tin("THIS_TIN_DOES_NOT_EXISTS") \
            .one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_company is None

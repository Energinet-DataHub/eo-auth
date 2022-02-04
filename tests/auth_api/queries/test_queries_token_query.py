from auth_api.db import db
from auth_api.queries import TokenQuery
from .query_base import TestQueryBase


class TestTokenQueries(TestQueryBase):
    """
    TODO
    """
    def test__has_opaque_token__opaque_token_exits__return_correct_opaque_token(
        self,
        seeded_session: db.Session,
        opaque_token: str,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        :param opaque_token:
        """

        # -- Act -------------------------------------------------------------

        query = TokenQuery(seeded_session)
        fetched_user = query.has_opaque_token(opaque_token).one_or_none()

        # -- Assert ----------------------------------------------------------
        assert fetched_user is not None
        assert fetched_user.opaque_token == opaque_token

    def test__has_subject__subject_does_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        """
        # -- Act -------------------------------------------------------------

        query = TokenQuery(seeded_session)
        fetched_user = query.has_opaque_token('INVALID_OPAQUE_TOKEN').one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_user is None

    """
    def test__token_is_valid__return_correct_issued_and_expires(
        self,
        seeded_session: db.Session,
        issued: str,
        expires: str,
    ):
    """

        #:param seeded_session: Mocked database session
        #:param opaque_token:
    """

        # -- Act -------------------------------------------------------------

        query = TokenQuery(seeded_session)
        fetched_user = query.is_valid(issued, expires).one_or_none()

        # -- Assert ----------------------------------------------------------
        assert fetched_user is not None
        assert fetched_user.opaque_token == opaque_token

    def test__has_subject__subject_does_not_exists__return_none(
        self,
        seeded_session: db.Session,
    ):
    """
        # TODO

        #:param seeded_session: Mocked database session
    """
        # -- Act -------------------------------------------------------------

        query = TokenQuery(seeded_session)
        fetched_user = query.has_opaque_token('INVALID_OPAQUE_TOKEN').one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_user is None
    """
    

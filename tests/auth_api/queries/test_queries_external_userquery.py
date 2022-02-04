import pytest

from auth_api.db import db
from auth_api.queries import ExternalUserQuery
from .query_base import TestQueryBase, USER_EXTERNAL_LIST


class TestExternalUserQueries(TestQueryBase):
    """
    TODO
    """
    @pytest.mark.parametrize('user', USER_EXTERNAL_LIST)
    def test__has_external_subject__external_subject__exists__return_correct_external_user(
            self,
            seeded_session: db.Session,
            user,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        :param user: Current user inserted into the test
        """
        # -- Act -------------------------------------------------------------

        query = ExternalUserQuery(seeded_session)
        fetched_external_user = query.has_external_subject(user['external_subject']).one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_external_user is not None
        assert fetched_external_user.external_subject == user['external_subject']

    def test__has_external_subject__external_subject_does_not_exists__return_none(
            self,
            seeded_session: db.Session,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        """
        # -- Act -------------------------------------------------------------

        query = ExternalUserQuery(seeded_session)
        fetched_user = query.has_external_subject('invalid_external_subject').one_or_none()

        # -- Assert ----------------------------------------------------------

        assert fetched_user is None

    @pytest.mark.parametrize('identity_provider', ['midid', 'nemid', 'invalid_nemid'])
    def test__has_identity_provider__identity_provider__exists__return_correct_external_user(
            self,
            seeded_session: db.Session,
            identity_provider,
    ):
        """
        TODO

        :param seeded_session: Mocked database session
        :param identity_provider: Current identity provider inserted into the test
        """
        # -- Arrange ---------------------------------------------------------

        seeded_users = [user for user in USER_EXTERNAL_LIST if user['identity_provider'] == identity_provider]

        # -- Act -------------------------------------------------------------

        query = ExternalUserQuery(seeded_session)
        fetched_external_users = query.has_identity_provider(identity_provider).all()

        # -- Assert ----------------------------------------------------------

        assert all(user.identity_provider == identity_provider for user in fetched_external_users)
        assert len(seeded_users) == len(fetched_external_users)

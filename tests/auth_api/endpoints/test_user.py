"""Tests user information."""
import pytest
from flask.testing import FlaskClient


class TestUserInformation(object):
    """Test user information."""

    @pytest.mark.unittest
    def test__user_info__returns_unauthorized_without_authorization(
            self,
            client: FlaskClient,
    ):
        # """When no token provided return 401."""

        # -- Act -------------------------------------------------------------

        res = client.get('/user/info')

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 401
        assert 'Authorization' not in res.headers

    def test__user_info__returns_unauthorized_without_a_valid_authorization(
            self,
            client: FlaskClient,
    ):
        # """When invalid token provided return 401."""

        # -- Act -------------------------------------------------------------

        res = client.get('/user/info', headers={'Authorization': 'not valid'})

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 401
        assert 'Authorization' not in res.headers

    def test__user_info__returns_info_with_correct_request(
            self,
            client: FlaskClient,
            internal_token_encoded: str
    ):
        # """When proper token provided return user info."""

        # -- Act -------------------------------------------------------------

        res = client.get('/user/info', headers={'Authorization': 'Bearer: ' + internal_token_encoded})  # noqa E501

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 200
        assert 'Authorization' in res.headers

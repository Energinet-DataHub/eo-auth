"""Tests specifically for OIDC login endpoint."""
# Standard Library
from urllib.parse import parse_qs, urlsplit

# Third party
import pytest
from flask.testing import FlaskClient

# First party
from origin.tokens import TokenEncoder

# Local
from auth_api.endpoints import AuthState

# -- Helpers -----------------------------------------------------------------


def get_auth_state_from_redirect_url(
        auth_url: str,
        state_encoder: TokenEncoder[AuthState],
) -> AuthState:
    """
    Get auth state from redirect url.

    Provided a HTTP redirect Location from a OIDC login endpoint, this
    method extract the 'state' query-parameter and decodes it for easy
    assertion.

    :param auth_url: The auth-URL returned by OIDC login endpoint
    :param state_encoder: The AuthState encoder
    :returns: Decoded AuthState object
    """
    url = urlsplit(auth_url)
    query = parse_qs(url.query)
    state_encoded = query['state'][0]
    return state_encoder.decode(state_encoded)


# -- Tests -------------------------------------------------------------------


class TestOidcLogin:
    """Tests specifically for OIDC login endpoint."""

    @pytest.mark.unittest
    def test__should_return_auth_url_as_json_with_correct_state(
            self,
            client: FlaskClient,
            state_encoder: TokenEncoder[AuthState],
    ):
        """
        Should return auth_url as json with correct state.

        Omitting the 'redirect' parameter should result in the endpoint
        returning the auth URL as part of JSON body.
        """

        # -- Act -------------------------------------------------------------

        res = client.get(
            path='/oidc/login',
            query_string={
                'fe_url': 'https://spam.com/',
                'return_url': 'https://foobar.com/',
            },
        )

        # -- Assert ----------------------------------------------------------

        actual_state = get_auth_state_from_redirect_url(
            auth_url=res.json['next_url'],
            state_encoder=state_encoder,
        )

        assert res.status_code == 200
        assert actual_state.return_url == 'https://foobar.com/'
        assert actual_state.fe_url == 'https://spam.com/'

    @pytest.mark.unittest
    def test__omit_parameter_return_url__should_return_status_400(
            self,
            client: FlaskClient,
    ):
        """
        Omitting the 'return_url' parameter should result in the endpoint.

        Returning HTTP status 400 Bad Request.
        """

        # -- Act -------------------------------------------------------------

        res = client.get(
            path='/oidc/login',
            query_string={
                # Missing parameter "return_url"
                'fe_url': 'https://spam.com/'
            },
        )

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 400

    @pytest.mark.unittest
    def test__omit_parameter_fe_url__should_return_status_400(
            self,
            client: FlaskClient,
    ):
        """
        Omitting the 'fe_url' parameter should result in the endpoint.

        returning HTTP status 400 Bad Request.
        """

        # -- Act -------------------------------------------------------------

        res = client.get(
            path='/oidc/login',
            query_string={
                # Missing parameter "fe_url"
                'return_url': 'https://foobar.com/',
            },
        )

        # -- Assert ----------------------------------------------------------

        assert res.status_code == 400

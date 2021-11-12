"""
Tests specifically for OIDC login endpoint.
"""
from flask.testing import FlaskClient
from urllib.parse import parse_qs, urlsplit

from energytt_platform.tokens import TokenEncoder

from auth_api.endpoints import AuthState


# -- Helpers -----------------------------------------------------------------


def get_auth_state_from_redirect_url(
        auth_url: str,
        state_encoder: TokenEncoder[AuthState],
) -> AuthState:
    """
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
    """
    Tests specifically for OIDC login endpoint.
    """

    def test__should_return_auth_url_as_json_with_correct_state(
            self,
            client: FlaskClient,
            state_encoder: TokenEncoder[AuthState],
    ):
        """
        Omitting the 'redirect' parameter should result in the endpoint
        returning the auth URL as part of JSON body.
        """

        # -- Act -------------------------------------------------------------

        r = client.get(
            path='/oidc/login',
            query_string={
                'return_url': 'http://foobar.com/',
            },
        )

        # -- Assert ----------------------------------------------------------

        actual_state = get_auth_state_from_redirect_url(
            auth_url=r.json['url'],
            state_encoder=state_encoder,
        )

        assert r.status_code == 200
        assert actual_state.return_url == 'http://foobar.com/'

    def test__omit_parameter_return_url__should_return_status_400(
            self,
            client: FlaskClient,
    ):
        """
        Omitting the 'return_url' parameter should result in the endpoint
        returning HTTP status 400 Bad Request.
        """

        # -- Act -------------------------------------------------------------

        r = client.get(
            path='/oidc/login',
            query_string={},  # Missing parameter "redirect_uri"
        )

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 400

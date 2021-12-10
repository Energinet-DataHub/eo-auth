"""
Tests specifically for OIDC login endpoint.
"""
from datetime import datetime, timezone, timedelta

import pytest
from flask.testing import FlaskClient

from origin.models.auth import InternalToken
from origin.tokens import TokenEncoder


class TestGetProfile:
    """
    TODO
    """

    @pytest.mark.unittest
    def test__should_return_auth_url_as_json_with_correct_state(
            self,
            client: FlaskClient,
            token_encoder: TokenEncoder[InternalToken],
    ):
        """
        Omitting the 'redirect' parameter should result in the endpoint
        returning the auth URL as part of JSON body.
        """

        # -- Act -------------------------------------------------------------

        token = InternalToken(
            issued=datetime.now(tz=timezone.utc),
            expires=datetime.now(tz=timezone.utc) + timedelta(days=1),
            actor='actor',
            subject='subject',
            scope=['scope1', 'scope2'],
        )

        token_encoded = token_encoder.encode(token)

        r = client.get(
            path='/profile',
            headers={
                'Authorization': f'Bearer: {token_encoded}',
            },
        )

        # -- Assert ----------------------------------------------------------

        assert r.status_code == 200
        assert r.json == {
            'success': True,
            'profile': {
                'id': token.actor,
                'name': 'John Doe',  # TODO
                'company': 'New Company',  # TODO
                'scope': ['scope1', 'scope2'],
            }
        }

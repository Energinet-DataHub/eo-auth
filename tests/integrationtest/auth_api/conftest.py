"""
conftest.py according to pytest docs:
https://docs.pytest.org/en/2.7.3/plugins.html?highlight=re#conftest-py-plugins
"""
import pytest
from uuid import uuid4
from typing import Dict, Any
from unittest.mock import patch
from authlib.jose import jwt, jwk
from flask.testing import FlaskClient
from datetime import datetime, timezone, timedelta

from energytt_platform.tokens import TokenEncoder

from auth_api.app import create_app
from auth_api.endpoints import AuthState
from auth_api.config import INTERNAL_TOKEN_SECRET

from .keys import PRIVATE_KEY, PUBLIC_KEY


# -- API ---------------------------------------------------------------------


@pytest.fixture(scope='function')
def client() -> FlaskClient:
    """
    Returns API test client.
    """
    return create_app().test_client


# -- OAuth2 session methods --------------------------------------------------


@pytest.fixture(scope='function')
def mock_get_jwk():
    """
    Returns a mock of OAuth2Session.get_jwk() method.
    """
    with patch('auth_api.oidc.session.get_jwk') as get_jwk:
        yield get_jwk


@pytest.fixture(scope='function')
def mock_fetch_token():
    """
    Returns a mock of OAuth2Session.fetch_token() method.
    """
    with patch('auth_api.oidc.session.fetch_token') as fetch_token:
        yield fetch_token


@pytest.fixture(scope='function')
def state_encoder() -> TokenEncoder[AuthState]:
    """
    Returns AuthState encoder with correct secret embedded.
    """
    return TokenEncoder(
        schema=AuthState,
        secret=INTERNAL_TOKEN_SECRET,
    )


# -- Keys & Security ---------------------------------------------------------


@pytest.fixture(scope='function')
def jwk_public() -> str:
    """
    Mocked public key from Identity Provider.
    """
    return jwk.dumps(PUBLIC_KEY, kty='RSA')


@pytest.fixture(scope='function')
def jwk_private() -> str:
    """
    Mocked private key from Identity Provider.
    """
    return jwk.dumps(PRIVATE_KEY, kty='RSA')


# -- Tokens ------------------------------------------------------------------


@pytest.fixture(scope='function')
def token_subject() -> str:
    """
    Identity Provider's subject (used in mocked tokens).
    """
    return str(uuid4())


@pytest.fixture(scope='function')
def token_idp() -> str:
    """
    Identity Provider's name (used in mocked tokens).

    Could be, for instance, 'mitid' or 'nemid'.
    """
    return 'mitid'


@pytest.fixture(scope='function')
def token_ssn() -> str:
    """
    Identity Provider's social security number (used in mocked tokens).
    """
    return str(uuid4())


@pytest.fixture(scope='function')
def token_issued() -> datetime:
    """
    Time of issue Identity Provider's token.
    """
    return datetime.now(tz=timezone.utc)


@pytest.fixture(scope='function')
def token_expires(token_issued: datetime) -> datetime:
    """
    Time of expire Identity Provider's token.
    """
    return token_issued + timedelta(days=1)


@pytest.fixture(scope='function')
def ip_token(
    id_token_encoded: str,
    userinfo_token_encoded: str,
    token_expires: datetime,
) -> Dict[str, Any]:
    """
    Mocked token from Identity Provider (unencoded).
    """
    return {
        'id_token': id_token_encoded,
        'access_token': '',
        'expires_in': 3600,
        'token_type': 'Bearer',
        'scope': 'openid mitid nemid ssn userinfo_token',
        'userinfo_token': userinfo_token_encoded,
        'expires_at': int(token_expires.timestamp()),
    }


@pytest.fixture(scope='function')
def id_token(
        token_subject: str,
        token_idp: str,
        token_issued: datetime,
        token_expires: datetime,
) -> Dict[str, Any]:
    """
    Mocked ID-token from Identity Provider (unencoded).
    """
    return {
        'iss': 'https://pp.netseidbroker.dk/op',
        'nbf': 1632389546,
        'iat': int(token_issued.timestamp()),
        'exp': int(token_expires.timestamp()),
        'auth_time': int(token_issued.timestamp()),
        'aud': str(uuid4()),
        'amr': ['code_app'],
        'at_hash': '-Y-YJBoneGN5sEk6vawM9A',
        'sub': token_subject,
        'idp': token_idp,
        'acr': 'https://data.gov.dk/concept/core/nsis/Substantial',
        'neb_sid': str(uuid4()),
        'loa': 'https://data.gov.dk/concept/core/nsis/Substantial',
        'identity_type': 'private',
        'transaction_id': str(uuid4()),
        'session_expiry': '1632403505',
    }


@pytest.fixture(scope='function')
def id_token_encoded(
        jwk_private: str,
        id_token: Dict[str, Any],
) -> str:
    """
    Mocked ID-token from Identity Provider (encoded).
    """
    token = jwt.encode(
        header={'alg': 'RS256'},
        payload=id_token,
        key=jwk_private,
    )

    return token.decode()


@pytest.fixture(scope='function')
def userinfo_token(
        token_subject: str,
        token_idp: str,
        token_ssn: str,
) -> Dict[str, Any]:
    """
    Mocked userinfo-token from Identity Provider (unencoded).
    """
    return {
        'iss': 'https://pp.netseidbroker.dk/op',
        'nbf': 1632389572,
        'iat': 1632389572,
        'exp': 1632389872,
        'amr': ['code_app'],
        'mitid.uuid': '7ddb51e7-5a04-41f8-9f3c-eec1d9444979',
        'mitid.age': '55',
        'mitid.identity_name': 'Anker Andersen',
        'mitid.date_of_birth': '1966-02-03',
        'loa': 'https://data.gov.dk/concept/core/nsis/Substantial',
        'acr': 'https://data.gov.dk/concept/core/nsis/Substantial',
        'identity_type': 'private',
        'idp': token_idp,
        'dk.cpr': token_ssn,
        'auth_time': '1632387312',
        'sub': token_subject,
        'aud': '0a775a87-878c-4b83-abe3-ee29c720c3e7',
        'transaction_id': 'a805f253-e8ea-4457-9996-c67bf704ab4a',
    }


@pytest.fixture(scope='function')
def userinfo_token_encoded(
        jwk_private: str,
        userinfo_token: Dict[str, Any],
) -> str:
    """
    Mocked userinfo-token from Identity Provider (encoded).
    """
    token = jwt.encode(
        header={'alg': 'RS256'},
        payload=userinfo_token,
        key=jwk_private,
    )

    return token.decode()

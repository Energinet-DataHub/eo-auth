"""
Tests specifically for OIDC login endpoint.
"""
import pytest

from auth_api.config import TOKEN_COOKIE_SAMESITE, TOKEN_COOKIE_SECURE


@pytest.mark.unittest
def test__token_cookie_samesite__value_omitted__should_return_default_true():
    """
    Omitting the 'TOKEN_COOKIE_SAMESITE' option should make
    it default to True.
    """

    assert TOKEN_COOKIE_SAMESITE is True


@pytest.mark.unittest
def test__token_cookie_secure__value_omitted__should_return_default_true():
    """
    Omitting the 'TOKEN_COOKIE_SECURE' option should make
    it default to True.
    """

    assert TOKEN_COOKIE_SECURE is True

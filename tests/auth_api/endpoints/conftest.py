import pytest

from origin.models.auth import InternalToken
from origin.tokens import TokenEncoder

from auth_api.config import INTERNAL_TOKEN_SECRET


@pytest.fixture(scope='module')
def token_encoder() -> TokenEncoder[InternalToken]:
    """
    Returns InternalToken encoder with correct secret embedded.
    """
    return TokenEncoder(
        schema=InternalToken,
        secret=INTERNAL_TOKEN_SECRET,
    )

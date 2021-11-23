from typing import Optional
from dataclasses import dataclass, field

from origin.api import Endpoint, Context


@dataclass
class UserProfile:
    id: str
    name: str
    company: Optional[str] = field(default=None)


class GetProfile(Endpoint):
    """
    An endpoint the returns the user's (actor's) profile.
    """

    @dataclass
    class Response:
        success: bool
        profile: UserProfile

    def handle_request(self, context: Context) -> Response:
        """
        Handle HTTP request.
        """
        return self.Response(
            success=True,
            profile=UserProfile(
                # id=context.token.actor,
                id='1234',
                name='John Doe',
                company=None,
            ),
        )

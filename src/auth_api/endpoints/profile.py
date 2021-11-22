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
        profile: UserProfile

    def handle_request(self, context: Context) -> Response:
        """
        Handle HTTP request.
        """
        return self.Response(
            profile=UserProfile(
                id=context.token.actor,
                name='',
                company=None,
            ),
        )

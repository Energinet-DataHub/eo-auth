from typing import Optional, List
from dataclasses import dataclass, field

from origin.api import Endpoint, Context


@dataclass
class UserProfile:
    id: str
    name: str
    scope: List[str] = field(field(default_factory=list))
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
                id=context.token.actor,
                name='John Doe',
                company=None,
                scope=context.token.scope,
            ),
        )

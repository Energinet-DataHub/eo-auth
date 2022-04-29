# Standard Library
from dataclasses import dataclass

# First party
from origin.api import (
    Context,
    Endpoint,
    HttpError,
)
from origin.api.responses import Unauthorized

# Local
from auth_api.queries import UserQuery
from auth_api.db import db


class GetUserInformation(Endpoint):
    """Call to retrieve information about the current user."""

    @dataclass
    class Response:
        """A model of the information related to the current user."""

        subject: str
        tin: str

    @db.session()
    def handle_request(
            self,
            context: Context,
            session: db.Session,
    ) -> Response:
        """
        Handle HTTP request.

        :param context: Context for a single HTTP request.
        """

        if not context.token:
            raise Unauthorized()

        user = UserQuery(session) \
            .has_subject(context.token.subject) \
            .one_or_none()

        if not user:
            raise HttpError(msg="User not found", status=404)

        return self.Response(
            subject=user.subject,
            tin=user.tin,
        )

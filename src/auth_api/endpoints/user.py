# Standard Library
from dataclasses import dataclass

# First party
from origin.api import (
    Context,
    Endpoint,
    HttpError,
)

# Local
from auth_api.queries import UserQuery
from auth_api.db import db


class GetUserInformation(Endpoint):
    """TODO."""

    @dataclass
    class Response:
        """TODO."""

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

        user = UserQuery(session) \
            .has_subject(context.token.subject) \
            .one_or_none()

        if not user:
            raise HttpError(msg="User not found", status=404)

        print("user", user)

        return self.Response(
            subject=user.subject,
            tin=user.tin,
        )

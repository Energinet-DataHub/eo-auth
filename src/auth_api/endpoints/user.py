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

        try:
            print('headers', context.headers)
            print('internal_token_encoded', context.internal_token_encoded)
            internal_token = context.token_encoder.decode(context.internal_token_encoded)  # noqa 501
            print('internal_token', internal_token)
            print('is_valid', internal_token.is_valid)
        except context.token_encoder.DecodeError as a_a:
            print('error', a_a)

        user = UserQuery(session) \
            .has_subject(context.token.subject) \
            .one_or_none()

        if not user:
            raise HttpError(msg="User not found", status=404)

        return self.Response(
            subject=user.subject,
            tin=user.tin,
        )

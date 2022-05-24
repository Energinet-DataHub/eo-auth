# Standard Library
from dataclasses import dataclass
from typing import Optional

# First party
from origin.api import (
    Context,
    Endpoint,
    HttpError,
)
from origin.api.responses import Unauthorized

# Local
from auth_api.queries import CompanyQuery, UserQuery
from auth_api.db import db


class GetUserInformation(Endpoint):
    """Call to retrieve information about the current user."""

    @dataclass
    class Response:
        """A model of the information related to the current user."""

        subject: str
        tin: Optional[str]

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

        user_id = context.token.actor

        # This is an assumption that hte token subject is the id of a company
        # We can only make this assumption as long as users can only login
        # on the behalf of a company. Later users can loging on behalf of
        # other users, which makes this a wrong assumption.
        company_id = context.token.subject

        user = UserQuery(session) \
            .has_subject(user_id) \
            .one_or_none()

        company = CompanyQuery(session) \
            .has_id(company_id) \
            .one_or_none()

        if not user:
            raise HttpError(msg="User not found", status=404)

        return self.Response(
            subject=user.subject,
            tin=company.tin if company else None,
        )

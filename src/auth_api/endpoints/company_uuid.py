from dataclasses import dataclass
from origin.api import Endpoint, HttpError
from auth_api.controller import db_controller
from auth_api.db import db


class GetCompanyId(Endpoint):
    """Endpoint for getting company id."""

    @dataclass
    class Request:
        """Model for getting request tin."""

        cvr: str

    @dataclass
    class Response:
        """Model for returning response."""

        uuid: str

    @db.session()
    def handle_request(
        self,
        request: Request,
        session: db.session,
    ) -> Response:
        """
        Handle HTTP Request.

        :param cvr: a cvr number is passed
        """

        company_profile = db_controller.get_company_by_tin(
            session=session,
            tin=request.cvr
        )

        if company_profile is None:
            raise HttpError(msg="Company not found", status=404)

        return self.Response(
            uuid=company_profile.id
        )

from dataclasses import dataclass
from origin.api import Endpoint
from auth_api.controller import db_controller
from auth_api.db import db


class GetUserUuid(Endpoint):
    """Endpoint for getting user uuid"""

    @dataclass
    class Request:
        """Model for getting request tin"""
        cvr: str

    @dataclass
    class Response:
        """Model for returning response"""
        uuid: str

    @db.session()
    def handle_request(
        self,
        request: Request,
        session: db.session,
    ) -> Response:

        company_uuid = db_controller.get_company_by_tin(
            session=session,
            tin=request.cvr
        )

        return self.Response(
            uuid=company_uuid
        )

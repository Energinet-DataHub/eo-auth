# Standard Library
import os
from dataclasses import dataclass
from tkinter import Tcl

# Third party
import markdown2

# First party
from origin.api import (
    BadRequest,
    Context,
    Endpoint,
    HttpResponse,
)

# Local
from auth_api.config import TERMS_MARKDOWN_FOLDER
from auth_api.db import db
from auth_api.orchestrator import (
    LoginOrchestrator,
    LoginResponse,
    state_encoder,
)
from auth_api.state import build_failure_url


class GetTerms(Endpoint):
    """
    An endpoint which returns the terms and conditions.
    """

    @dataclass
    class Response:
        headline: str
        terms: str
        version: str

    def handle_request(self, context: Context) -> Response:
        """
        Handle HTTP request.
        """
        file_list = os.listdir(TERMS_MARKDOWN_FOLDER)

        newest_file = Tcl().call('lsort', '-decreasing', file_list)[0]

        filepath = f'{TERMS_MARKDOWN_FOLDER}/{newest_file}'
        version = newest_file.split('.')[0]

        try:
            with open(filepath) as file:
                markdown_content = file.read()
        except Exception:
            raise RuntimeError("An error occured reading the markdown file")

        try:
            html = markdown2.markdown(markdown_content)
            return self.Response(
                headline='Privacy Policy',
                terms=html,
                version=version,
            )
        except Exception:
            raise RuntimeError("An error occured converting markdown to html")


class AcceptTerms(Endpoint):
    """
    An endpoint which marks a user as having accepted terms and conditions.
    """

    @dataclass
    class Request:
        state: str
        accepted: bool
        version: str

    @db.atomic()
    def handle_request(
        self,
        request: Request,
        context: Context,
        session: db.Session,
    ) -> HttpResponse:
        """
        Handle HTTP request.
        """
        # Decode state
        try:
            state = state_encoder.decode(request.state)
        except state_encoder.DecodeError:
            # TODO Handle...
            raise BadRequest()

        # TODO Verify accepted version is valid?

        state.terms_accepted = request.accepted
        state.terms_version = request.version

        orchestrator = LoginOrchestrator(
            session=session,
            state=state,
        )

        if request.accepted:
            return orchestrator.response_next_step()
        else:
            url = build_failure_url(
                state=state,
                error_code='E4'
            )

            return HttpResponse(
                status=200,
                model=LoginResponse(
                    next_url=url,
                )
            )

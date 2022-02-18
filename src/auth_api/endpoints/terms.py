import markdown2

from dataclasses import dataclass

from origin.api import Endpoint, Context, BadRequest, HttpResponse

from auth_api.db import db
from auth_api.config import TERMS_MARKDOWN_PATH
from auth_api.state import build_failure_url
from auth_api.orchestrator import (
    state_encoder,
    LoginOrchestrator,
    LoginResponse,
)


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

        try:
            with open(TERMS_MARKDOWN_PATH) as file:
                markdown_content = file.read()
        except Exception:
            raise RuntimeError("An error occured reading the markdown file")

        try:
            html = markdown2.markdown(markdown_content)
            return self.Response(
                headline='Privacy Policy',
                terms=html,
                version='0.1',
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

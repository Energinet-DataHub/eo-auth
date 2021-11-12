from dataclasses import dataclass

from energytt_platform.tokens import TokenEncoder
from energytt_platform.auth import TOKEN_HEADER_NAME
from energytt_platform.models.auth import InternalToken
from energytt_platform.api import (
    Endpoint,
    Context,
    HttpResponse,
    Unauthorized,
)

from auth_api.db import db
from auth_api.queries import TokenQuery
from auth_api.config import INTERNAL_TOKEN_SECRET


class ForwardAuth(Endpoint):
    """
    ForwardAuth endpoint for Træfik.

    https://doc.traefik.io/traefik/v2.0/middlewares/forwardauth/
    """

    def handle_request(self, context: Context) -> HttpResponse:
        """
        Handle HTTP request.
        """
        if not context.opaque_token:
            raise Unauthorized()

        internal_token = self.get_internal_token(context.opaque_token)

        if internal_token is None:
            raise Unauthorized()

        return HttpResponse(
            status=200,
            headers={
                TOKEN_HEADER_NAME: f'Bearer: {internal_token}',
            },
        )

    @db.session()
    def get_internal_token(
            self,
            opaque_token: str,
            session: db.Session,
    ) -> str:
        """
        TODO

        :param opaque_token:
        :param session:
        """
        token = TokenQuery(session) \
            .has_opaque_token(opaque_token) \
            .is_valid() \
            .one_or_none()

        if token:
            return token.internal_token


class InspectToken(Endpoint):
    """
    TODO
    """

    @dataclass
    class Response:
        token: InternalToken

    def handle_request(self, context: Context) -> Response:
        """
        Handle HTTP request.
        """
        return self.Response(
            token=context.token,
        )


class CreateTestToken(Endpoint):
    """
    Creates a new token (for testing purposes).
    """

    @dataclass
    class Request:
        token: InternalToken

    @dataclass
    class Response:
        token: str

    def handle_request(self, request: Request, context: Context) -> Response:
        """
        Handle HTTP request.
        """
        encoder = TokenEncoder(
            schema=InternalToken,
            secret=INTERNAL_TOKEN_SECRET,
        )

        return self.Response(
            token=encoder.encode(request.token),
        )

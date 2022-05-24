# Local
from auth_api.controller import db_controller
from auth_api.db import db
from auth_api.models import DbUser
from auth_api.state import AuthState


def create_or_get_user(
        session: db.Session,
        state: AuthState
) -> DbUser:
    """
    Create or get a user and an external user if they don't exist.

    This only happens if they have accepted terms

    :param session: The db session
    :param state: AuthState
    :return: A DbUser if a user has been created or exists, otherwise an error
    """

    if not state.terms_accepted:
        raise RuntimeError("User has not accepted terms")

    user = db_controller.get_user_by_external_subject(
        session=session,
        identity_provider=state.identity_provider,
        external_subject=state.external_subject,
    )

    if not user:
        user = db_controller.get_or_create_user(
            session=session,
        )

        db_controller.attach_external_user(
            session=session,
            user=user,
            external_subject=state.external_subject,
            identity_provider=state.identity_provider,
        )

    return user

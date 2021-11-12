from .app import create_app
from .config import DEVELOP_HOST, DEVELOP_PORT


create_app().run_debug(
    host=DEVELOP_HOST,
    port=DEVELOP_PORT,
)

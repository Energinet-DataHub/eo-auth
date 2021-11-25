from .app import create_app
from .config import DEVELOP_PORT


create_app().run_debug(
    host='0.0.0.0',
    port=DEVELOP_PORT,
)

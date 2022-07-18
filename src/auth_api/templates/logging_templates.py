from datetime import datetime

import logging
import json

"""Set logging"""
logger = logging.getLogger()
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)


class LoggingTemplates:
    """Logs a message with the given level."""

    def __init__(self, log_level=None) -> None:
        self.log_level = log_level

    def log(self, message, actor, subject) -> None:
        """TODO"""
        time_stamp = datetime.now().strftime('%Y-%m-%dT%Y:%H:%M:%S.%f')

        json_dict = {"Timestamp": time_stamp,
                     "Level": self.log_level,
                     "MessageTemplate": message,
                     "Properties": {
                         "ActorId": actor,
                         "Subject": subject
                     }
                     }
        logger.info(json.dumps(json_dict))

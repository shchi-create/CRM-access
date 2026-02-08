import logging
from typing import Optional


class SafeLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return msg, kwargs



def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )



def get_logger(name: str, user_id: Optional[str] = None) -> SafeLoggerAdapter:
    logger = logging.getLogger(name)
    return SafeLoggerAdapter(logger, {"user_id": user_id})

import logging
import platform
import traceback
import warnings
from typing import Any, Callable, Dict

from .backend import KartonBackend
from .task import get_current_task

HOSTNAME = platform.node()


class TaskContextFilter(logging.Filter):
    """
    This is a filter which injects information about current task ID to the log.
    """



class LogLineFormatterMixin:
    format: Callable[[logging.LogRecord], str]



class KartonLogHandler(logging.Handler, LogLineFormatterMixin):
    """
    logging.Handler that passes logs to the Karton backend.
    """

    def __init__(self, backend: KartonBackend, channel: str) -> None:
        logging.Handler.__init__(self)
        self.backend = backend
        self.is_consumer_active: bool = True
        self.channel: str = channel


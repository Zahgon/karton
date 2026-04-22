"""
asyncio implementation of KartonLogHandler
"""
import asyncio
import logging
import platform
from typing import Any, Dict, Optional, Tuple
from karton.core.logger import LogLineFormatterMixin
from .backend import KartonAsyncBackend
HOSTNAME = platform.node()
QueuedRecord = Optional[Tuple[Dict[str, Any], str]]

async def async_log_consumer(queue: asyncio.Queue[QueuedRecord], backend: KartonAsyncBackend, channel: str) -> None:
    pass

class KartonAsyncLogHandler(logging.Handler, LogLineFormatterMixin):
    """
    logging.Handler that passes logs to the Karton backend.
    """

    def __init__(self, backend: KartonAsyncBackend, channel: str) -> None:
        logging.Handler.__init__(self)
        self._consumer: Optional[asyncio.Task] = None
        self._queue: asyncio.Queue[QueuedRecord] = asyncio.Queue()
        self._backend = backend
        self._channel = channel

    def emit(self, record: logging.LogRecord) -> None:
        pass

    def start_consuming(self):
        pass

    async def stop_consuming(self):
        pass

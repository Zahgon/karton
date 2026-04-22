import abc
import asyncio
import signal
from asyncio import CancelledError
from typing import Optional
from karton.core import Task
from karton.core.__version__ import __version__
from karton.core.backend import KartonServiceInfo
from karton.core.base import ConfigMixin, LoggingMixin
from karton.core.config import Config
from karton.core.task import get_current_task, set_current_task
from karton.core.utils import StrictClassMethod
from .backend import KartonAsyncBackend
from .logger import KartonAsyncLogHandler

class KartonAsyncBase(abc.ABC, ConfigMixin, LoggingMixin):
    """
    Base class for all Karton services

    You can set an informative version information by setting the ``version`` class
    attribute.
    """
    identity: str = ''
    version: Optional[str] = None
    with_service_info: bool = False

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonAsyncBackend]=None) -> None:
        ConfigMixin.__init__(self, config, identity)
        self.service_info = None
        if self.identity is not None and self.with_service_info:
            self.service_info = KartonServiceInfo(identity=self.identity, karton_version=__version__, service_version=self.version)
        self.backend = backend or KartonAsyncBackend(self.config, identity=self.identity, service_info=self.service_info)
        log_handler = KartonAsyncLogHandler(backend=self.backend, channel=self.identity)
        LoggingMixin.__init__(self, log_handler, log_format='[%(asctime)s][%(levelname)s][%(task_id)s] %(message)s')

    async def connect(self) -> None:
        pass

class KartonAsyncServiceBase(KartonAsyncBase):
    """
    Karton base class for looping services.

    You can set an informative version information by setting the ``version`` class
    attribute

    :param config: Karton config to use for service configuration
    :param identity: Karton service identity to use
    :param backend: Karton backend to use
    """

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonAsyncBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)
        self.setup_logger()
        self._loop_coro: Optional[asyncio.Task] = None

    @abc.abstractmethod
    async def _loop(self) -> None:
        pass

    async def loop(self) -> None:
        pass

    @StrictClassMethod
    def main(cls) -> None:
        """Main method invoked from CLI."""
        pass

import abc
import argparse
import asyncio
import sys
import time
import traceback
from asyncio import CancelledError
from typing import Any, Dict, List, Optional
from karton.core import query
from karton.core.__version__ import __version__
from karton.core.backend import KartonBind, KartonMetrics
from karton.core.config import Config
from karton.core.exceptions import TaskTimeoutError
from karton.core.task import Task, TaskState
from .backend import KartonAsyncBackend
from .base import KartonAsyncBase, KartonAsyncServiceBase
from .resource import LocalResource

class Producer(KartonAsyncBase):
    """
    Producer part of Karton. Used for dispatching initial tasks into karton.

    :param config: Karton configuration object (optional)
    :type config: :class:`karton.Config`
    :param identity: Producer name (optional)
    :type identity: str

    Usage example:

    .. code-block:: python

        from karton.core.asyncio import Producer

        producer = Producer(identity="karton.mwdb")
        await producer.connect()
        task = Task(
            headers={
                "type": "sample",
                "kind": "raw"
            },
            payload={
                "sample": Resource("sample.exe", b"put content here")
            }
        )
        await producer.send_task(task)

    :param config: Karton config to use for service configuration
    :param identity: Karton producer identity
    :param backend: Karton backend to use
    """

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonAsyncBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)

    async def send_task(self, task: Task) -> bool:
        """
        Sends a task to the unrouted task queue. Takes care of logging.
        Given task will be child of task we are currently handling (if such exists).

        :param task: Task object to be sent
        :return: Bool indicating if the task was delivered
        """
        pass

class Consumer(KartonAsyncServiceBase):
    """
    Base consumer class, this is the part of Karton responsible for processing
    incoming tasks

    :param config: Karton config to use for service configuration
    :param identity: Karton service identity
    :param backend: Karton backend to use
    :param task_timeout: The maximum time, in seconds, this consumer will wait for
                         a task to finish processing before being CRASHED on timeout.
                         Set 0 for unlimited, and None for using global value
    :param concurrency_limit: The maximum number of concurrent tasks that may be
                        gathered from queue and processed asynchronously.
    """
    filters: List[Dict[str, Any]] = []
    persistent: bool = True
    version: Optional[str] = None
    task_timeout = None
    concurrency_limit: Optional[int] = 1

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonAsyncBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)
        if self.filters is None:
            raise ValueError('Cannot bind consumer on Empty binds')
        query.convert(self.filters)
        self.persistent = self.config.getboolean('karton', 'persistent', self.persistent) and (not self.debug)
        if self.task_timeout is None:
            self.task_timeout = self.config.getint('karton', 'task_timeout')
        self.concurrency_limit = self.config.getint('karton', 'concurrency_limit', self.concurrency_limit)
        self.concurrency_semaphore: Optional[asyncio.Semaphore] = None
        if self.concurrency_limit is not None:
            self.concurrency_semaphore = asyncio.BoundedSemaphore(self.concurrency_limit)

    @abc.abstractmethod
    async def process(self, task: Task) -> None:
        """
        Task processing method.

        :param task: The incoming task object

        self.current_task contains task that triggered invocation of
        :py:meth:`karton.Consumer.process` but you should only focus on the passed
        task object and shouldn't interact with the field directly.
        """
        pass

    async def _internal_process(self, task: Task) -> None:
        pass

    async def internal_process(self, task: Task) -> None:
        """
        The internal side of :py:meth:`Consumer.process` function, takes care of
        synchronizing the task state, handling errors and running task hooks.

        :param task: Task object to process

        :meta private:
        """
        pass

    @classmethod
    def args_parser(cls) -> argparse.ArgumentParser:
        pass

    @classmethod
    def config_from_args(cls, config: Config, args: argparse.Namespace) -> None:
        pass

    async def _loop(self) -> None:
        """
        Blocking loop that consumes tasks and runs
        :py:meth:`karton.Consumer.process` as a handler

        :meta private:
        """
        pass

class Karton(Consumer, Producer):
    """
    This glues together Consumer and Producer - which is the most common use case
    """

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonAsyncBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)

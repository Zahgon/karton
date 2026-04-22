"""
Base library for karton subsystems.
"""
import abc
import argparse
import sys
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, cast
from . import query
from .__version__ import __version__
from .backend import KartonBackend, KartonBind, KartonMetrics
from .base import KartonBase, KartonServiceBase
from .config import Config
from .exceptions import TaskTimeoutError
from .resource import LocalResource
from .task import Task, TaskState
from .utils import timeout

class Producer(KartonBase):
    """
    Producer part of Karton. Used for dispatching initial tasks into karton.

    :param config: Karton configuration object (optional)
    :type config: :class:`karton.Config`
    :param identity: Producer name (optional)
    :type identity: str

    Usage example:

    .. code-block:: python

        from karton.core import Producer

        producer = Producer(identity="karton.mwdb")
        task = Task(
            headers={
                "type": "sample",
                "kind": "raw"
            },
            payload={
                "sample": Resource("sample.exe", b"put content here")
            }
        )
        producer.send_task(task)

    :param config: Karton config to use for service configuration
    :param identity: Karton producer identity
    :param backend: Karton backend to use
    """

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)

    def send_task(self, task: Task) -> bool:
        """
        Sends a task to the unrouted task queue. Takes care of logging.
        Given task will be child of task we are currently handling (if such exists).

        :param task: Task object to be sent
        :return: Bool indicating if the task was delivered
        """
        pass

class Consumer(KartonServiceBase):
    """
    Base consumer class, this is the part of Karton responsible for processing
    incoming tasks

    :param config: Karton config to use for service configuration
    :param identity: Karton service identity
    :param backend: Karton backend to use
    :param task_timeout: The maximum time, in seconds, this consumer will wait for
                         a task to finish processing before being CRASHED on timeout.
                         Set 0 for unlimited, and None for using global value
    """
    filters: List[Dict[str, Any]] = []
    persistent: bool = True
    version: Optional[str] = None
    task_timeout = None

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)
        if self.filters is None:
            raise ValueError('Cannot bind consumer on Empty binds')
        query.convert(self.filters)
        self.persistent = self.config.getboolean('karton', 'persistent', self.persistent) and (not self.debug)
        if self.task_timeout is None:
            self.task_timeout = self.config.getint('karton', 'task_timeout')
        self._pre_hooks: List[Tuple[Optional[str], Callable[[Task], None]]] = []
        self._post_hooks: List[Tuple[Optional[str], Callable[[Task, Optional[BaseException]], None]]] = []

    @abc.abstractmethod
    def process(self, task: Task) -> None:
        """
        Task processing method.

        :param task: The incoming task object

        self.current_task contains task that triggered invocation of
        :py:meth:`karton.Consumer.process` but you should only focus on the passed
        task object and shouldn't interact with the field directly.
        """
        pass

    def internal_process(self, task: Task) -> None:
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

    def add_pre_hook(self, callback: Callable[[Task], None], name: Optional[str]=None) -> None:
        """
        Add a function to be called before processing each task.

        :param callback: Function of the form ``callback(task)`` where ``task``
            is a :class:`karton.Task`
        :param name: Name of the pre-hook
        """
        pass

    def add_post_hook(self, callback: Callable[[Task, Optional[BaseException]], None], name: Optional[str]=None) -> None:
        """
        Add a function to be called after processing each task.

        :param callback: Function of the form ``callback(task, exception)``
            where ``task`` is a :class:`karton.Task` and ``exception`` is
            an exception thrown by the :meth:`karton.Consumer.process` function
            or ``None``.
        :param name: Name of the post-hook
        """
        pass

    def _run_pre_hooks(self) -> None:
        """
        Run registered preprocessing hooks

        :meta private:
        """
        pass

    def _run_post_hooks(self, exception: Optional[BaseException]) -> None:
        """
        Run registered postprocessing hooks

        :param exception: Exception object that was caught while processing the task

        :meta private:
        """
        pass

    def loop(self) -> None:
        """
        Blocking loop that consumes tasks and runs
        :py:meth:`karton.Consumer.process` as a handler

        :meta private:
        """
        pass

class LogConsumer(KartonServiceBase):
    """
    Base class for log consumer subsystems.

    You can consume logs from specific logger
    by setting a :py:meth:`logger_filter` class attribute.

    You can also select logs of specific level via
    :py:meth:`level` class attribute.

    :param config: Karton config to use for service configuration
    :param identity: Karton service identity
    :param backend: Karton backend to use
    """
    logger_filter: Optional[str] = None
    level: Optional[str] = None
    with_service_info = True

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)

    @abc.abstractmethod
    def process_log(self, event: Dict[str, Any]) -> None:
        """
        The core log handler that should be overwritten in implemented log handlers

        :param event: Dictionary containing the log event data
        """
        pass

    def loop(self) -> None:
        """
        Internal loop that consumes the log queues and deals with exceptions
        and graceful exits

        :meta private:
        """
        pass

class Karton(Consumer, Producer):
    """
    This glues together Consumer and Producer - which is the most common use case
    """

    def __init__(self, config: Optional[Config]=None, identity: Optional[str]=None, backend: Optional[KartonBackend]=None) -> None:
        super().__init__(config=config, identity=identity, backend=backend)
        if self.config.getboolean('signaling', 'status', fallback=False):
            self.log.info('Using status signaling')
            self.add_pre_hook(self._send_signaling_status_task_begin, 'task_begin')
            self.add_post_hook(self._send_signaling_status_task_end, 'task_end')

    def _send_signaling_status_task_begin(self, task: Task) -> None:
        """Send a begin status signaling task.

        :meta private:
        """
        pass

    def _send_signaling_status_task_end(self, task: Task, ex: Optional[BaseException]) -> None:
        """Send a begin status signaling task.

        :meta private:
        """
        pass

    def _send_signaling_status_task(self, status: str) -> None:
        """Send a status signaling task.

        :param status: Status task identifier.

        :meta private:
        """
        pass

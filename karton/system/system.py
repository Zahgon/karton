import argparse
import json
import time
from typing import List, Optional
from karton.core import query
from karton.core.__version__ import __version__
from karton.core.backend import KARTON_OPERATIONS_QUEUE, KARTON_TASKS_QUEUE, KartonBind, KartonMetrics
from karton.core.base import KartonServiceBase
from karton.core.config import Config
from karton.core.task import Task, TaskState
from karton.core.utils import StrictClassMethod

class SystemService(KartonServiceBase):
    """
    Karton message broker.
    """
    identity = 'karton.system'
    version = __version__
    with_service_info = True
    CRASH_STARTED_TASKS_ON_TIMEOUT = False
    GC_INTERVAL = 3 * 60
    TASK_DISPATCHED_TIMEOUT = 24 * 3600
    TASK_STARTED_TIMEOUT = 24 * 3600
    TASK_CRASHED_TIMEOUT = 3 * 24 * 3600
    TASK_TRACKING_TTL = 30 * 24 * 3600

    def __init__(self, config: Optional[Config]) -> None:
        super().__init__(config=config)
        self.gc_interval = self.config.getint('system', 'gc_interval', self.GC_INTERVAL)
        self.task_dispatched_timeout = self.config.getint('system', 'task_dispatched_timeout', self.TASK_DISPATCHED_TIMEOUT)
        self.task_started_timeout = self.config.getint('system', 'task_started_timeout', self.TASK_STARTED_TIMEOUT)
        self.task_crashed_timeout = self.config.getint('system', 'task_crashed_timeout', self.TASK_CRASHED_TIMEOUT)
        self.enable_gc = self.config.getboolean('system', 'enable_gc', True)
        self.enable_router = self.config.getboolean('system', 'enable_router', True)
        self.crash_started_tasks_on_timeout = self.config.getboolean('system', 'crash_started_tasks_on_timeout', False)
        self.enable_null_version_deletion = self.config.getboolean('system', 'enable_null_version_deletion', False)
        self.enable_task_tracking = self.config.getboolean('system', 'enable_task_tracking', True)
        self.task_tracking_ttl = self.config.getint('system', 'task_tracking_ttl', self.TASK_TRACKING_TTL)
        self.last_gc_trigger = time.time()

    def _log_config(self):
        pass

    def gc_collect_resources(self) -> None:
        pass

    def gc_collect_tasks(self) -> None:
        pass

    def gc_collect(self) -> None:
        pass

    def route_task(self, task: Task, binds: List[KartonBind]) -> None:
        pass

    def handle_tasks(self, task_uids: List[str]) -> None:
        pass

    def handle_operations(self, bodies: List[str]) -> None:
        """
        Left for backwards compatibility with Karton <=4.3.0.
        Earlier versions delegate task status change to karton.system.
        """
        pass

    def process_routing(self) -> None:
        pass

    def loop(self) -> None:
        pass

    @classmethod
    def args_parser(cls) -> argparse.ArgumentParser:
        pass

    @classmethod
    def config_from_args(cls, config: Config, args: argparse.Namespace):
        pass

    def ensure_bucket_exists(self, create: bool) -> bool:
        pass

    @StrictClassMethod
    def main(cls) -> None:
        pass

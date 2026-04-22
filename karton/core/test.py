"""
Test stubs for karton subsystem unit tests
"""
import hashlib
import logging
import unittest
from collections import defaultdict
from typing import Any, BinaryIO, Dict, List, Optional, Union, cast
from unittest import mock
from .backend import KartonBackend, KartonMetrics
from .config import Config
from .resource import LocalResource, RemoteResource, ResourceBase
from .task import Task, TaskState
__all__ = ['KartonTestCase', 'mock']
log = logging.getLogger()

class ConfigMock(Config):

    def __init__(self):
        self._config = {'redis': {}, 's3': {}}

class BackendMock:

    def __init__(self) -> None:
        self.produced_tasks: List[Task] = []
        self.buckets: Dict[str, Dict[str, bytes]] = defaultdict(dict)

    def declare_task(self, task: Task) -> None:
        pass

    def set_task_status(self, task: Task, status: TaskState, pipe=None) -> None:
        pass

    def produce_unrouted_task(self, task: Task) -> None:
        pass

    def produce_log(self, log_record: Dict[str, Any], logger_name: str, level: str) -> bool:
        pass

    def increment_metrics(self, metric: KartonMetrics, identity: str) -> None:
        pass

    def upload_object(self, bucket: str, object_uid: str, content: Union[bytes, BinaryIO], length: Optional[int]=None) -> None:
        pass

    def upload_object_from_file(self, bucket: str, object_uid: str, path: str) -> None:
        pass

class KartonTestCase(unittest.TestCase):
    """
    Unit test case class

    .. code-block:: python
        from cutter import Cutter

        class CutterTestCase(KartonTestCase):
            karton_class = Cutter

        def test_karton_service(self):
            resource = Resource('incoming', b'put content here')
            task = Task({
                'type': 'string'
            }, payload={
                'chars': 6,
                'sample': resource
            })
            results = self.run_task(task)
            self.assertTasksEqual(results, [
                Task({
                    'origin': 'karton.cutter',
                    'type': 'cutted_string'
                }, payload={
                    'sample': Resource('outgoing', b'put co')
                })
            ])
    """
    karton_class = None
    config = None
    kwargs = None

    def get_resource_sha256(self, resource: ResourceBase) -> str:
        """
        Calculate SHA256 hash for a given resource

        :param resource: Resource to be hashed
        :return: Hex-encoded SHA256 digest
        """
        pass

    def assertResourceEqual(self, resource: ResourceBase, expected: ResourceBase, resource_name: str) -> None:
        """Assert that two resources are equal

        :param resource: Output resource
        :param expected: Expected resource
        :param resource_name: Resource name
        """
        pass

    def assertTaskEqual(self, task: Task, expected: Task) -> None:
        """
        Assert that two task objects are equal

        :param task: Result task
        :param expected: Expected task
        """
        pass

    def assertTasksEqual(self, tasks: List[Task], expected: List[Task]) -> None:
        """
        Assert that two task lists are equal

        :param tasks: Result tasks list
        :param expected: Expected tasks list
        """
        pass

    def _process_task(self, incoming_task: Task):
        """
        Converts task from outgoing to incoming including transformation
        of LocalResources to RemoteResources
        """
        pass

    def run_task(self, task: Task) -> List[Task]:
        """
        Spawns task into tested Karton subsystem instance

        :param task: Task to be spawned
        :return: Result tasks sent by Karton Service
        """
        pass
TestResource = LocalResource

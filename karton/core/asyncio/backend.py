import json
import logging
import os
import time
from typing import IO, Any, Dict, List, Optional, Tuple, Union
import aioboto3
from aiobotocore.credentials import ContainerProvider, InstanceMetadataProvider
from aiobotocore.session import ClientCreatorContext, get_session
from aiobotocore.utils import InstanceMetadataFetcher
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from redis.exceptions import AuthenticationError
from karton.core import Config, Task
from karton.core.asyncio.resource import LocalResource, RemoteResource
from karton.core.backend import KARTON_BINDS_HSET, KARTON_TASK_NAMESPACE, KARTON_TASKS_QUEUE, KartonBackendBase, KartonBind, KartonMetrics, KartonServiceInfo
from karton.core.resource import LocalResource as SyncLocalResource
from karton.core.task import TaskState
logger = logging.getLogger(__name__)

class KartonAsyncBackend(KartonBackendBase):

    def __init__(self, config: Config, identity: Optional[str]=None, service_info: Optional[KartonServiceInfo]=None) -> None:
        super().__init__(config, identity, service_info)
        self._redis: Optional[Redis] = None
        self._s3_session: Optional[aioboto3.Session] = None
        self._s3_iam_auth = False

    async def connect(self):
        pass

    async def iam_auth_s3(self):
        pass

    @classmethod
    async def make_redis(cls, config, identity: Optional[str]=None, service_info: Optional[KartonServiceInfo]=None) -> Redis:
        """
        Create and test a Redis connection.

        :param config: The karton configuration
        :param identity: Karton service identity
        :param service_info: Additional service identity metadata
        :return: Redis connection
        """
        pass

    def unserialize_resource(self, resource_spec: Dict[str, Any]) -> RemoteResource:
        """
        Unserializes resource into a RemoteResource object bound with current backend

        :param resource_spec: Resource specification
        :return: RemoteResource object
        """
        pass

    async def declare_task(self, task: Task) -> None:
        """
        Declares a new task to send it to the queue.

        :param task: Task to declare
        """
        pass

    async def register_task(self, task: Task, pipe: Optional[Pipeline]=None) -> None:
        """
        Register or update task in Redis.

        :param task: Task object
        :param pipe: Optional pipeline object if operation is a part of pipeline
        """
        pass

    async def set_task_status(self, task: Task, status: TaskState, pipe: Optional[Pipeline]=None) -> None:
        """
        Request task status change to be applied by karton-system

        :param task: Task object
        :param status: New task status (TaskState)
        :param pipe: Optional pipeline object if operation is a part of pipeline
        """
        pass

    async def register_bind(self, bind: KartonBind) -> Optional[KartonBind]:
        """
        Register bind for Karton service and return the old one

        :param bind: KartonBind object with bind definition
        :return: Old KartonBind that was registered under this identity
        """
        pass

    async def get_bind(self, identity: str) -> KartonBind:
        """
        Get bind object for given identity

        :param identity: Karton service identity
        :return: KartonBind object
        """
        pass

    async def produce_unrouted_task(self, task: Task) -> None:
        """
        Add given task to unrouted task (``karton.tasks``) queue

        Task must be registered before with :py:meth:`register_task`

        :param task: Task object
        """
        pass

    async def consume_queues(self, queues: Union[str, List[str]], timeout: int=0) -> Optional[Tuple[str, str]]:
        """
        Get item from queues (ordered from the most to the least prioritized)
        If there are no items, wait until one appear.

        :param queues: Redis queue name or list of names
        :param timeout: Waiting for item timeout (default: 0 = wait forever)
        :return: Tuple of [queue_name, item] objects or None if timeout has been reached
        """
        pass

    async def get_task(self, task_uid: str) -> Optional[Task]:
        """
        Get task object with given identifier

        :param task_uid: Task identifier
        :return: Task object
        """
        pass

    async def consume_routed_task(self, identity: str, timeout: int=5) -> Optional[Task]:
        """
        Get routed task for given consumer identity.

        If there are no tasks, blocks until new one appears or timeout is reached.

        :param identity: Karton service identity
        :param timeout: Waiting for task timeout (default: 5)
        :return: Task object
        """
        pass

    async def increment_metrics(self, metric: KartonMetrics, identity: str, pipe: Optional[Pipeline]=None) -> None:
        """
        Increments metrics for given operation type and identity

        :param metric: Operation metric type
        :param identity: Related Karton service identity
        :param pipe: Optional pipeline object if operation is a part of pipeline
        """
        pass

    async def upload_object(self, bucket: str, object_uid: str, content: Union[bytes, IO[bytes]]) -> None:
        """
        Upload resource object to underlying object storage (S3)

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :param content: Object content as bytes or file-like stream
        """
        pass

    async def upload_object_from_file(self, bucket: str, object_uid: str, path: str) -> None:
        """
        Upload resource object file to underlying object storage

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :param path: Path to the object content
        """
        pass

    async def download_object(self, bucket: str, object_uid: str) -> bytes:
        """
        Download resource object from object storage.

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :return: Content bytes
        """
        pass

    async def download_object_to_file(self, bucket: str, object_uid: str, path: str) -> None:
        """
        Download resource object from object storage to file

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :param path: Target file path
        """
        pass

    async def produce_log(self, log_record: Dict[str, Any], logger_name: str, level: str) -> bool:
        """
        Push new log record to the logs channel

        :param log_record: Dict with log record
        :param logger_name: Logger name
        :param level: Log level
        :return: True if any active log consumer received log record
        """
        pass

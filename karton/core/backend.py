import dataclasses
import enum
import json
import logging
import os
import time
import urllib.parse
import warnings
from collections import defaultdict, namedtuple
from typing import IO, Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union
import boto3
from botocore.credentials import ContainerProvider, InstanceMetadataFetcher, InstanceMetadataProvider
from botocore.session import get_session
from redis import AuthenticationError, StrictRedis
from redis.client import Pipeline
from urllib3.response import HTTPResponse
from .config import Config
from .exceptions import InvalidIdentityError
from .resource import LocalResource, RemoteResource
from .task import Task, TaskPriority, TaskState
from .utils import chunks, chunks_iter
KARTON_TASKS_QUEUE = 'karton.tasks'
KARTON_OPERATIONS_QUEUE = 'karton.operations'
KARTON_LOG_CHANNEL = 'karton.log'
KARTON_BINDS_HSET = 'karton.binds'
KARTON_TASK_NAMESPACE = 'karton.task'
KARTON_OUTPUTS_NAMESPACE = 'karton.outputs'
KartonBind = namedtuple('KartonBind', ['identity', 'info', 'version', 'persistent', 'filters', 'service_version', 'is_async'])
KartonOutputs = namedtuple('KartonOutputs', ['identity', 'outputs'])
logger = logging.getLogger(__name__)

class KartonMetrics(enum.Enum):
    TASK_PRODUCED = 'karton.metrics.produced'
    TASK_CONSUMED = 'karton.metrics.consumed'
    TASK_CRASHED = 'karton.metrics.crashed'
    TASK_ASSIGNED = 'karton.metrics.assigned'
    TASK_GARBAGE_COLLECTED = 'karton.metrics.garbage-collected'

@dataclasses.dataclass(frozen=True, order=True)
class KartonServiceInfo:
    """
    Extended Karton service information.

    Instances of this dataclass are meant to be aggregated to count service replicas
    in Karton Dashboard. They're considered equal if identity and versions strings
    are the same.
    """
    identity: str = dataclasses.field(metadata={'serializable': False})
    karton_version: str
    service_version: Optional[str] = None
    redis_client_info: Optional[Dict[str, str]] = dataclasses.field(default=None, hash=False, compare=False, metadata={'serializable': False})

    def make_client_name(self) -> str:
        pass

class KartonBackendBase:

    def __init__(self, config: Config, identity: Optional[str]=None, service_info: Optional[KartonServiceInfo]=None):
        self.config = config
        if identity is not None:
            self._validate_identity(identity)
        self.identity = identity
        self.service_info = service_info

    @staticmethod
    def get_redis_configuration(config: Config, identity: Optional[str]=None, service_info: Optional[KartonServiceInfo]=None) -> Dict[str, Any]:
        pass

    @staticmethod
    def get_queue_name(identity: str, priority: TaskPriority) -> str:
        """
        Return Redis routed task queue name for given identity and priority

        :param identity: Karton service identity
        :param priority: Queue priority (TaskPriority enum value)
        :return: Queue name
        """
        pass

    @staticmethod
    def get_queue_names(identity: str) -> List[str]:
        """
        Return all Redis routed task queue names for given identity,
        ordered by priority (descending). Used internally by Consumer.

        :param identity: Karton service identity
        :return: List of queue names
        """
        pass

    @staticmethod
    def serialize_bind(bind: KartonBind) -> str:
        """
        Serialize KartonBind object (Karton service registration)

        :param bind: KartonBind object with bind definition
        :return: Serialized bind data
        """
        pass

    @staticmethod
    def unserialize_bind(identity: str, bind_data: str) -> KartonBind:
        """
        Deserialize KartonBind object for given identity.
        Compatible with Karton 2.x.x and 3.x.x

        :param identity: Karton service identity
        :param bind_data: Serialized bind data
        :return: KartonBind object with bind definition
        """
        pass

    @staticmethod
    def unserialize_output(identity: str, output_data: Set[str]) -> KartonOutputs:
        """
        Deserialize KartonOutputs object for given identity.

        :param identity: Karton service identity
        :param output_data: Serialized output data
        :return: KartonOutputs object with outputs definition
        """
        pass

    @staticmethod
    def _log_channel(logger_name: Optional[str], level: Optional[str]) -> str:
        pass

class KartonBackend(KartonBackendBase):

    def __init__(self, config: Config, identity: Optional[str]=None, service_info: Optional[KartonServiceInfo]=None) -> None:
        super().__init__(config, identity, service_info)
        self.redis = self.make_redis(config, identity=identity, service_info=service_info)
        endpoint = config.get('s3', 'address') or os.getenv('AWS_ENDPOINT_URL')
        access_key = config.get('s3', 'access_key') or os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = config.get('s3', 'secret_key') or os.getenv('AWS_SECRET_ACCESS_KEY')
        iam_auth = config.getboolean('s3', 'iam_auth')
        if not endpoint:
            raise RuntimeError('Attempting to get S3 client without an endpoint set')
        if access_key and secret_key and iam_auth:
            logger.warning('Warning: iam is turned on and both S3 access key and secret key are provided')
        if iam_auth:
            s3_client = self.iam_auth_s3(endpoint)
            if s3_client:
                self.s3 = s3_client
                return
        if access_key is None or secret_key is None:
            raise RuntimeError('Attempting to get S3 client without an access_key/secret_key set')
        self.s3 = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    def iam_auth_s3(self, endpoint: str):
        pass

    @classmethod
    def make_redis(cls, config, identity: Optional[str]=None, service_info: Optional[KartonServiceInfo]=None) -> StrictRedis:
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

    def get_bind(self, identity: str) -> KartonBind:
        """
        Get bind object for given identity

        :param identity: Karton service identity
        :return: KartonBind object
        """
        pass

    def get_binds(self) -> List[KartonBind]:
        """
        Get all binds registered in Redis

        :return: List of KartonBind objects for subsequent identities
        """
        pass

    def register_bind(self, bind: KartonBind) -> Optional[KartonBind]:
        """
        Register bind for Karton service and return the old one

        :param bind: KartonBind object with bind definition
        :return: Old KartonBind that was registered under this identity
        """
        pass

    def unregister_bind(self, identity: str) -> None:
        """
        Removes bind for identity
        :param bind: Identity to be unregistered
        """
        pass

    def set_consumer_identity(self, _: str) -> None:
        """
        Sets identity for current Redis connection
        """
        pass

    def get_online_consumers(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Gets all online identities.

        Actually this method returns all services having an identity,
        so the list is not limited to consumers.

        :return: Dictionary {identity: [list of clients]}
        """
        pass

    def get_online_services(self) -> List[KartonServiceInfo]:
        """
        Gets all online services providing extended service information.

        Consumers by default don't provide that information and it's included in binds
        instead. If you want to get information about all services, use
        :py:meth:`KartonBackend.get_online_consumers`.

        .. versionadded:: 5.1.0

        :return: List of KartonServiceInfo objects
        """
        pass

    def get_task(self, task_uid: str) -> Optional[Task]:
        """
        Get task object with given identifier

        :param task_uid: Task identifier
        :return: Task object
        """
        pass

    def get_tasks(self, task_uid_list: List[str], chunk_size: int=1000, parse_resources: bool=True) -> List[Task]:
        """
        Get multiple tasks for given identifier list

        :param task_uid_list: List of task identifiers
        :param chunk_size: Size of chunks passed to the Redis MGET command
        :param parse_resources: If set to False, resources are not parsed.
            It speeds up deserialization. Read :py:meth:`Task.unserialize`
            documentation to learn more.
        :return: List of task objects
        """
        pass

    def _iter_tasks(self, task_keys: Iterator[str], chunk_size: int=1000, parse_resources: bool=True) -> Iterator[Task]:
        pass

    def iter_tasks(self, task_uid_list: Iterable[str], chunk_size: int=1000, parse_resources: bool=True) -> Iterator[Task]:
        """
        Get multiple tasks for given identifier list as an iterator
        :param task_uid_list: List of task fully-qualified identifiers
        :param chunk_size: Size of chunks passed to the Redis MGET command
        :param parse_resources: If set to False, resources are not parsed.
            It speeds up deserialization. Read :py:meth:`Task.unserialize` documentation
            to learn more.
        :return: Iterator with task objects
        """
        pass

    def iter_all_tasks(self, chunk_size: int=1000, parse_resources: bool=True) -> Iterator[Task]:
        """
        Iterates all tasks registered in Redis
        :param chunk_size: Size of chunks passed to the Redis SCAN and MGET command
        :param parse_resources: If set to False, resources are not parsed.
            It speeds up deserialization. Read :py:meth:`Task.unserialize` documentation
            to learn more.
        :return: Iterator with Task objects
        """
        pass

    def get_all_tasks(self, chunk_size: int=1000, parse_resources: bool=True) -> List[Task]:
        """
        Get all tasks registered in Redis

        .. warning::
            This method loads all tasks into memory.
            It's recommended to use :py:meth:`iter_all_tasks` instead.

        :param chunk_size: Size of chunks passed to the Redis MGET command
        :param parse_resources: If set to False, resources are not parsed.
            It speeds up deserialization. Read :py:meth:`Task.unserialize` documentation
            to learn more.
        :return: List with Task objects
        """
        pass

    def _iter_legacy_task_tree(self, root_uid: str, chunk_size: int=1000, parse_resources: bool=True) -> Iterator[Task]:
        """
        Processes tasks made by <5.4.0 (unrouted from <5.4.0 producers or existing
        before upgrade)

        Used internally by iter_task_tree.
        """
        pass

    def iter_task_tree(self, root_uid: str, chunk_size: int=1000, parse_resources: bool=True) -> Iterator[Task]:
        """
        Iterates all tasks that belong to the same analysis task tree
        and have the same root_uid

        :param root_uid: Root identifier of task tree
        :param chunk_size: Size of chunks passed to the Redis SCAN and MGET command
        :param parse_resources: If set to False, resources are not parsed.
            It speeds up deserialization. Read :py:meth:`Task.unserialize` documentation
            to learn more.
        :return: Iterator with task objects
        """
        pass

    def declare_task(self, task: Task) -> None:
        """
        Declares a new task to send it to the queue.

        Task producers should use this method for new tasks.

        :param task: Task to declare
        """
        pass

    def register_task(self, task: Task, pipe: Optional[Pipeline]=None) -> None:
        """
        Register or update task in Redis.

        This method is used internally to alter task data. If you want to declare new
        task in Redis, use declare_task.

        :param task: Task object
        :param pipe: Optional pipeline object if operation is a part of pipeline
        """
        pass

    def register_tasks(self, tasks: List[Task]) -> None:
        """
        Register or update multiple tasks in Redis.
        :param tasks: List of task objects
        """
        pass

    def set_task_status(self, task: Task, status: TaskState, pipe: Optional[Pipeline]=None) -> None:
        """
        Request task status change to be applied by karton-system

        :param task: Task object
        :param status: New task status (TaskState)
        :param pipe: Optional pipeline object if operation is a part of pipeline
        """
        pass

    def delete_task(self, task: Task) -> None:
        """
        Remove task from Redis

        .. warning::
            Used internally by karton.system.
            If you want to cancel task: mark it as finished and let it be deleted
            by karton.system.

        :param task: Task object
        """
        pass

    def delete_tasks(self, tasks: Iterable[Task], chunk_size: int=1000) -> None:
        """
        Remove multiple tasks from Redis

        .. warning::
            Used internally by karton.system.
            If you want to cancel task: mark it as finished and let it be deleted
            by karton.system.

        :param tasks: List of Task objects
        :param chunk_size: Size of chunks passed to the Redis DELETE command
        """
        pass

    def get_task_queue(self, queue: str) -> List[Task]:
        """
        Return all tasks in provided queue

        :param queue: Queue name
        :return: List with Task objects contained in queue
        """
        pass

    def get_task_ids_from_queue(self, queue: str) -> List[str]:
        """
        Return all task UIDs in a queue

        :param queue: Queue name
        :return: List with task identifiers contained in queue
        """
        pass

    def delete_consumer_queues(self, identity: str) -> None:
        """
        Deletes consumer queues for given identity

        :param identity: Consumer identity
        """
        pass

    def remove_task_queue(self, queue: str) -> List[Task]:
        """
        Remove task queue with all contained tasks

        :param queue: Queue name
        :return: List with Task objects contained in queue
        """
        pass

    def produce_unrouted_task(self, task: Task) -> None:
        """
        Add given task to unrouted task (``karton.tasks``) queue

        Task must be registered before with :py:meth:`register_task`

        :param task: Task object
        """
        pass

    def produce_routed_task(self, identity: str, task: Task, pipe: Optional[Pipeline]=None) -> None:
        """
        Add given task to routed task queue of given identity

        Task must be registered using :py:meth:`register_task`

        :param identity: Karton service identity
        :param task: Task object
        :param pipe: Optional pipeline object if operation is a part of pipeline
        """
        pass

    def consume_queues(self, queues: Union[str, List[str]], timeout: int=0) -> Optional[Tuple[str, str]]:
        """
        Get item from queues (ordered from the most to the least prioritized)
        If there are no items, wait until one appear.

        :param queues: Redis queue name or list of names
        :param timeout: Waiting for item timeout (default: 0 = wait forever)
        :return: Tuple of [queue_name, item] objects or None if timeout has been reached
        """
        pass

    def increment_multiple_metrics(self, metric: KartonMetrics, increments: Dict[str, int]) -> None:
        """
        Increments metrics for multiple identities by given value via single pipeline
        :param metric: Operation metric type
        :param increments: Dictionary of Karton service identities and value
            to add to the metric
        """
        pass

    def consume_queues_batch(self, queue: str, max_count: int) -> List[str]:
        """
        Get a batch of items from the queue

        :param queue: Redis queue name
        :param max_count: Maximum batch count
        """
        pass

    def consume_routed_task(self, identity: str, timeout: int=5) -> Optional[Task]:
        """
        Get routed task for given consumer identity.

        If there are no tasks, blocks until new one appears or timeout is reached.

        :param identity: Karton service identity
        :param timeout: Waiting for task timeout (default: 5)
        :return: Task object
        """
        pass

    def restart_task(self, task: Task) -> Task:
        """
        Requeues consumed task back to the consumer queue.

        New task is created with new uid and can be consumed by any active replica.

        Original task is marked as finished.

        :param task: Task to be restarted
        :return: Restarted task object
        """
        pass

    def produce_log(self, log_record: Dict[str, Any], logger_name: str, level: str) -> bool:
        """
        Push new log record to the logs channel

        :param log_record: Dict with log record
        :param logger_name: Logger name
        :param level: Log level
        :return: True if any active log consumer received log record
        """
        pass

    def produce_logs(self, log_records: List[Dict[str, Any]], logger_name: str, level: str) -> None:
        """
        Push multiple log records to the logs channel

        :param log_records: List of dicts with log record
        :param logger_name: Logger name
        :param level: Log level
        """
        pass

    def consume_log(self, timeout: int=5, logger_filter: Optional[str]=None, level: Optional[str]=None) -> Iterator[Optional[Dict[str, Any]]]:
        """
        Subscribe to logs channel and yield subsequent log records
        or None if timeout has been reached.

        If you want to subscribe only to a specific logger name
        and/or log level, pass them via logger_filter and level arguments.

        :param timeout: Waiting for log record timeout (default: 5)
        :param logger_filter: Filter for name of consumed logger
        :param level: Log level
        :return: Dict with log record
        """
        pass

    def increment_metrics(self, metric: KartonMetrics, identity: str, pipe: Optional[Pipeline]=None) -> None:
        """
        Increments metrics for given operation type and identity

        :param metric: Operation metric type
        :param identity: Related Karton service identity
        :param pipe: Optional pipeline object if operation is a part of pipeline
        """
        pass

    def increment_metrics_list(self, metric: KartonMetrics, identities: List[str]) -> None:
        """
        Increments metrics for multiple identities via single pipeline

        :param metric: Operation metric type
        :param identities: List of Karton service identities
        """
        pass

    def get_metrics(self, metric: KartonMetrics) -> Dict[str, int]:
        """
        Get a {karton-identity: current-number-of-tasks} mapping for a given metric.

        :param metric: Operation metric type
        """
        pass

    def upload_object(self, bucket: str, object_uid: str, content: Union[bytes, IO[bytes]]) -> None:
        """
        Upload resource object to underlying object storage (S3)

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :param content: Object content as bytes or file-like stream
        """
        pass

    def upload_object_from_file(self, bucket: str, object_uid: str, path: str) -> None:
        """
        Upload resource object file to underlying object storage

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :param path: Path to the object content
        """
        pass

    def get_object(self, bucket: str, object_uid: str) -> HTTPResponse:
        """
        Get resource object stream with the content.

        Returned response should be closed after use to release network resources.
        To reuse the connection, it's required to call `response.release_conn()`
        explicitly.

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :return: Response object with content
        """
        pass

    def download_object(self, bucket: str, object_uid: str) -> bytes:
        """
        Download resource object from object storage.

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :return: Content bytes
        """
        pass

    def download_object_to_file(self, bucket: str, object_uid: str, path: str) -> None:
        """
        Download resource object from object storage to file

        :param bucket: Bucket name
        :param object_uid: Object identifier
        :param path: Target file path
        """
        pass

    def list_objects(self, bucket: str) -> List[str]:
        """
        List identifiers of stored resource objects

        :param bucket: Bucket name
        :return: List of object identifiers
        """
        pass

    def list_object_versions(self, bucket: str) -> Dict[str, List[str]]:
        """
        List version identifiers of stored resource objects
        :param bucket: Bucket name
        :return: Dictionary of object version identifiers {key: [version_ids, ...]}
        """
        pass

    def remove_object(self, bucket: str, object_uid: str) -> None:
        """
        Remove resource object from object storage

        :param bucket: Bucket name
        :param object_uid: Object identifier
        """
        pass

    def remove_objects(self, bucket: str, object_uids: Iterable[str]) -> None:
        """
        Bulk remove resource objects from object storage

        :param bucket: Bucket name
        :param object_uids: Object identifiers
        """
        pass

    def remove_object_versions(self, bucket: str, object_versions: Dict[str, List[str]], explicit_version_null: bool=False) -> None:
        """
        Bulk remove resource object versions from object storage

        :param bucket: Bucket name
        :param object_versions: Object version identifiers
        :param explicit_version_null: |
            Some S3 providers (e.g. MinIO) need a reference
            to "null" version explicitly when versioning is in suspended state. On the
            other hand, some providers refuse to delete "null" versions when bucket
            versioning is disabled.
            See also: https://github.com/CERT-Polska/karton/issues/273.
        """
        pass

    def check_bucket_exists(self, bucket: str, create: bool=False) -> bool:
        """
        Check if bucket exists and optionally create it if it doesn't.

        :param bucket: Bucket name
        :param create: Create bucket if doesn't exist
        :return: True if bucket exists yet
        """
        pass

    def log_identity_output(self, identity: str, headers: Dict[str, Any], task_tracking_ttl: int) -> None:
        """
        Store the type of task outputted for given producer to
        be used in tracking karton service connections.

        :param identity: producer identity
        :param headers: outputted headers
        :param task_tracking_ttl: expire time (in seconds)
        """
        pass

    def get_outputs(self) -> List[KartonOutputs]:
        """
        Get a list of the output types for each karton.

        :return: List of KartonOutputs
        """
        pass

    def make_pipeline(self, transaction: bool=False) -> Pipeline:
        pass

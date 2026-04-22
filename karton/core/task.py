import enum
import json
import time
import uuid
import warnings
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Tuple, Union
from . import query
from .resource import RemoteResource, ResourceBase
from .utils import recursive_iter, recursive_iter_with_keys, recursive_map
if TYPE_CHECKING:
    from .backend import KartonBackend
import orjson
current_task: ContextVar[Optional['Task']] = ContextVar('current_task')

def get_current_task() -> Optional['Task']:
    pass

def set_current_task(task: Optional['Task']):
    pass

class TaskState(enum.Enum):
    DECLARED = 'Declared'
    SPAWNED = 'Spawned'
    STARTED = 'Started'
    FINISHED = 'Finished'
    CRASHED = 'Crashed'

class TaskPriority(enum.Enum):
    HIGH = 'high'
    NORMAL = 'normal'
    LOW = 'low'

class Task(object):
    """
    Task representation with headers and resources.

    :param headers: Routing information for other systems, this is what allows for                     evaluation of given system usefulness for given task.                     Systems filter by these.
    :param payload: Any instance of :py:class:`dict` - contains resources                     and additional informations
    :param headers_persistent: Persistent headers for whole task subtree,                                propagated from initial task.
    :param payload_persistent: Persistent payload set for whole task subtree,                                propagated from initial task
    :param priority: Priority of whole task subtree,                      propagated from initial task like `payload_persistent`
    :param parent_uid: Id of a routed task that has created this task by a karton with                        :py:meth:`.send_task`
    :param root_uid: Id of an unrouted task that is the root of this         task's analysis tree
    :param orig_uid: Id of an unrouted (or crashed routed) task that was forked to                      create this task
    :param uid: This tasks unique identifier
    :param error: Traceback of a exception that happened while performing this task
    """
    __slots__ = ('uid', 'root_uid', 'orig_uid', 'parent_uid', 'error', 'headers', 'status', 'last_update', 'priority', 'payload', 'payload_persistent', '_headers_persistent_keys')

    def __init__(self, headers: Dict[str, Any], payload: Optional[Dict[str, Any]]=None, headers_persistent: Optional[Dict[str, Any]]=None, payload_persistent: Optional[Dict[str, Any]]=None, priority: Optional[TaskPriority]=None, parent_uid: Optional[str]=None, root_uid: Optional[str]=None, orig_uid: Optional[str]=None, uid: Optional[str]=None, error: Optional[List[str]]=None, _status: Optional[TaskState]=None, _last_update: Optional[float]=None) -> None:
        payload = payload or {}
        payload_persistent = payload_persistent or {}
        headers_persistent = headers_persistent or {}
        if not isinstance(payload, dict):
            raise ValueError('Payload should be an instance of a dict')
        if not isinstance(payload_persistent, dict):
            raise ValueError('Persistent payload should be an instance of a dict')
        if not isinstance(headers_persistent, dict):
            raise ValueError('Persistent headers should be an instance of a dict')
        if uid is None:
            task_uid = str(uuid.uuid4())
            if root_uid is None:
                self.root_uid = task_uid
            else:
                self.root_uid = root_uid
            self.uid = f'{{{self.root_uid}}}:{task_uid}'
        else:
            self.uid = uid
            if root_uid is None:
                raise ValueError('root_uid cannot be None when uid is not None')
            self.root_uid = root_uid
        self.orig_uid = orig_uid
        self.parent_uid = parent_uid
        self.error = error
        self.headers = {**headers, **headers_persistent}
        self._headers_persistent_keys = set(headers_persistent.keys())
        self.status = _status or TaskState.DECLARED
        self.last_update: float = _last_update or time.time()
        self.priority = priority or TaskPriority.NORMAL
        self.payload = dict(payload)
        self.payload_persistent = dict(payload_persistent)

    @staticmethod
    def fquid_to_uid(fquid: str) -> str:
        """
        Gets task uid from fully-qualified fquid ({root_uid}:task_uid)

        :return: Task uid
        """
        pass

    def fork_task(self) -> 'Task':
        """
        Fork task to transfer single task to many queues (but use different UID).

        Used internally by karton-system

        :return: Forked copy of the original task

        :meta private:
        """
        pass

    def derive_task(self, headers: Dict[str, Any]) -> 'Task':
        """
        Creates copy of task with different headers,
        useful for proxying resource with added metadata.

        .. code-block:: python

            class MZClassifier(Karton):
                identity = "karton.mz-classifier"
                filters = {
                    "type": "sample",
                    "kind": "raw"
                }

                def process(self, task: Task) -> None:
                    sample = task.get_resource("sample")
                    if sample.content.startswith(b"MZ"):
                        self.log.info("MZ detected!")
                        task = task.derive_task({
                            "type": "sample",
                            "kind": "exe"
                        })
                        self.send_task(task)
                    self.log.info("Not a MZ :<")

        .. versionchanged:: 3.0.0

            Moved from static method to regular method:

            :code:`Task.derive_task(headers, task)` must be
            ported to :code:`task.derive_task(headers)`

        :param headers: New headers for the task
        :return: Copy of task with new headers
        """
        pass

    def matches_filters(self, filters: List[Dict[str, Any]]) -> bool:
        """Check if a task matches the given filters"""
        pass

    def set_task_parent(self, parent: 'Task'):
        """
        Bind existing Task to parent task

        :param parent: Task to bind to

        :meta private:
        """
        pass

    def merge_persistent_payload(self, other_task: 'Task') -> None:
        """
        Merge persistent payload from another task

        :param other_task: Task from which to merge persistent payload

        :meta private:
        """
        pass

    def merge_persistent_headers(self, other_task: 'Task') -> None:
        """
        Merge persistent headers from another task

        :param other_task: Task from which to merge persistent headers

        :meta private:
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Transform task data into dictionary
        :return: Task data dictionary

        :meta private:
        """
        pass

    def serialize(self, indent: Optional[int]=None) -> str:
        """
        Serialize task data into JSON string
        :param indent: Indent to use while serializing
        :return: Serialized task data

        :meta private:
        """
        pass

    def walk_payload_bags(self) -> Iterator[Tuple[Dict[str, Any], str, Any]]:
        """
        Iterate over all payload bags and direct payloads contained in them

        Generates tuples (payload_bag, key, value)

        :return: An iterator over all task payload bags
        """
        pass

    def walk_payload_items(self) -> Iterator[Tuple[str, Any]]:
        """
        Iterate recursively over all payload items

        Generates tuples (path, value).

        :return: An iterator over all task payload values
        """
        pass

    def transform_payload_bags(self, func: Callable[[Any], Any]) -> None:
        """
        Recursively transform contents of all payload bags and payloads
        contained in them

        :meta private:
        """
        pass

    def iterate_resources(self) -> Iterator[ResourceBase]:
        """
        Get list of resource objects bound to Task

        .. versionchanged: 5.0.0
            Returns Resource values instead of tuples (key, value)

        :return: An iterator over all task resources
        """
        pass

    @staticmethod
    def unserialize(data: Union[str, bytes], backend: Optional['KartonBackend']=None, parse_resources: bool=True, resource_unserializer: Optional[Callable[[Dict], Any]]=None) -> 'Task':
        """
        Unserialize Task instance from JSON string

        :param data: JSON-serialized task
        :param backend: |
            Backend instance to be bound to RemoteResource objects.
            Deprecated: pass resource_unserializer instead.
        :param parse_resources: |
            If set to False (default is True), method doesn't
            deserialize '__karton_resource__' entries, which speeds up deserialization
            process. This flag is used mainly for multiple task processing e.g.
            filtering based on status.
            When resource deserialization is turned off, Task.unserialize will try
            to use faster 3rd-party JSON parser (orjson).
        :param resource_unserializer: |
            Resource factory used for deserialization of __karton_resource__
            dictionary values.
        :return: Unserialized Task object

        :meta private:
        """
        pass

    def __repr__(self) -> str:
        return self.serialize()

    def add_payload(self, name: str, content: Any, persistent: bool=False) -> None:
        """
        Add payload to task

        :param name: Name of the payload
        :param content: Payload to be added
        :param persistent: Flag if the payload should be persistent
        """
        pass

    def add_resource(self, name: str, resource: ResourceBase, persistent: bool=False) -> None:
        """
        Add resource to task.

        Alias for :py:meth:`add_payload`

        .. deprecated:: 3.0.0
           Use :meth:`add_payload` instead.

        :param name: Name of the resource
        :param resource: Resource to be added
        :param persistent: Flag if the resource should be persistent
        """
        pass

    def get_payload(self, name: str, default: Any=None) -> Any:
        """
        Get payload from task

        :param name: name of the payload
        :param default: Value to be returned if payload is not present
        :return: Payload content
        """
        pass

    def get_resource(self, name: str) -> ResourceBase:
        """
        Get resource from task.

        Ensures that payload contains an Resource object.
        If not - raises :class:`TypeError`

        :param name: Name of the resource to get
        :return: :py:class:`karton.ResourceBase` - resource with given name
        """
        pass

    def remove_payload(self, name: str) -> None:
        """
        Removes payload for the task

        If payload doesn't exist or is persistent - raises KeyError

        :param name: Payload name to be removed
        """
        pass

    def has_payload(self, name: str) -> bool:
        """
        Checks whether payload exists

        :param name: Name of the payload to be checked
        :return: If tasks payload contains a value with given name
        """
        pass

    def is_header_persistent(self, name: str) -> bool:
        """
        Checks whether header exists and is persistent

        :param name: Name of the header to be checked
        :return: If tasks header with given name is persistent
        """
        pass

    def is_payload_persistent(self, name: str) -> bool:
        """
        Checks whether payload exists and is persistent

        :param name: Name of the payload to be checked
        :return: If tasks payload with given name is persistent
        """
        pass

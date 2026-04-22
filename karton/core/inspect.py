from collections import defaultdict
from typing import Dict, List, Optional

from .backend import KartonBackend, KartonBind
from .task import Task, TaskState


class KartonQueue:
    """
    View object representing a Karton queue

    :param bind: :class:`KartonBind` object representing the queue bind
    :param tasks: List of tasks currently in queue
    :param state: :class:`KartonState` object to be used
    """

    def __init__(
        self, bind: KartonBind, tasks: List[Task], state: "KartonState"
    ) -> None:
        self.bind = bind
        self.tasks = tasks
        self.state = state

    @property
    def last_update(self) -> float:
        """Get the last task update from this queue"""
        pass

    @property
    def online_consumers_count(self) -> int:
        """Get number of consumers listening on this queue"""
        pass

    @property
    def pending_tasks(self) -> List[Task]:
        """Get queue pending tasks"""
        pass

    @property
    def crashed_tasks(self) -> List[Task]:
        """Get queue crashed tasks"""
        pass


class KartonAnalysis:
    """
    View object representing a Karton task analysis

    :param root_uid: Analysis root task uid
    :param tasks: List of tasks
    :param state: :class:`KartonState` object to be used
    """

    def __init__(self, root_uid: str, tasks: List[Task], state: "KartonState") -> None:
        self.root_uid = root_uid
        self.tasks = tasks
        self.state = state

    @property
    def last_update(self) -> float:
        """Check the last task update from the analysis"""
        pass

    @property
    def is_done(self) -> bool:
        """Check if the analysis is completely done"""
        pass

    @property
    def pending_tasks(self) -> List[Task]:
        """Get analysis pending tasks"""
        pass

    @property
    def pending_queues(self) -> Dict[str, KartonQueue]:
        """Group analysis tasks by their queues"""
        pass

    @property
    def crashed_tasks(self) -> List[Task]:
        """Get analysis crashed tasks"""
        pass


def get_queues_for_tasks(
    tasks: List[Task], state: "KartonState"
) -> Dict[str, KartonQueue]:
    """
    Group task objects by their queue name

    :param tasks: Task objects to group
    :param state: :class:`KartonState` object to be used
    :return: A dictionary containing the queue names and lists of tasks
    """
    pass


class KartonState:
    """
    Karton state inspection class. Allows to make a detailed inspection
    of the pipeline and analyses state.

    .. versionadded: 4.0.0

    :param backend: :py:meth:`KartonBackend` object to use for data fetching
    """

    def __init__(self, backend: KartonBackend, parse_resources: bool = False) -> None:
        self.backend = backend
        self.binds = {bind.identity: bind for bind in backend.get_binds()}
        self.replicas = backend.get_online_consumers()
        self.parse_resources = parse_resources

        self._tasks: Optional[List[Task]] = None
        self._pending_tasks: Optional[List[Task]] = None
        self._analyses: Optional[Dict[str, KartonAnalysis]] = None
        self._queues: Optional[Dict[str, KartonQueue]] = None






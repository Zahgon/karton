import functools
import itertools
import signal
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Sequence, Tuple, TypeVar
from .exceptions import HardShutdownInterrupt, TaskTimeoutError
T = TypeVar('T')

def chunks(seq: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    pass

def chunks_iter(seq: Iterator[T], size: int) -> Iterator[Sequence[T]]:
    pass

def recursive_iter(obj: Any) -> Iterator[Any]:
    """
    Yields all values recursively from nested list/dict structures

    :param obj: Object to iterate over
    """
    pass

def recursive_iter_with_keys(obj: Any, name: str='') -> Iterator[Tuple[str, Any]]:
    """
    Yields (path, value) tuples recursively from nested list/dict structures

    :param obj: Object to iterate over
    :param name: Object name
    """
    pass

def recursive_map(func: Callable[[Any], Any], obj: Any) -> Any:
    """
    Returns copy of collection with recursively mapped elements

    :param func: Mapping function
    :param obj: Object to iterate over
    """
    pass

@contextmanager
def timeout(wait_for: int):
    pass

@contextmanager
def graceful_killer(handler: Callable[[], None]):
    """
    Graceful killer for Karton consumers.
    """
    pass

class StrictClassMethod:
    """
    Like classmethod, but allows calling only when retrieved from class.

    Created to avoid ``KartonClass().main()`` pattern which leads to
    unexpected errors (correct form is ``KartonClass.main()``)
    """

    def __init__(self, func: Callable):
        self.func = func

    def __get__(self, instance: Any, owner: Any):
        return newfunc

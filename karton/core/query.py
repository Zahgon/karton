import fnmatch
import re
from collections.abc import Mapping, Sequence
from typing import Dict, Type

class QueryError(Exception):
    """Query error exception"""
    pass

class _Undefined(object):
    pass

def is_non_string_sequence(entry):
    """Returns True if entry is a Python sequence iterable, and not a string"""
    pass

class Query(object):
    """The Query class is used to match an object against a MongoDB-like query"""

    def __init__(self, definition, _type_coercion=False):
        """
        If _type_coercion is enabled: header values are coerced to string
        when condition is also a string. It's implemented for compatibility
        with old syntax e.g. {"execute": "!False"} filter vs {"execute": False}
        header value.
        """
        self._definition = definition
        self._type_coercion = _type_coercion

    def match(self, entry):
        """Matches the entry object against the query specified on instanciation"""
        pass

    def _match(self, condition, entry):
        pass

    def _extract(self, entry, path):
        pass

    def _path_exists(self, operator, condition, entry):
        pass

    def _process_condition(self, operator, condition, entry):
        pass

    @staticmethod
    def _not_implemented(*_):
        pass

    @staticmethod
    def _noop(*_):
        pass

    def _eq(self, condition, entry):
        pass
    _exists = _noop
    _options = _text = _where = _not_implemented

    def __repr__(self):
        return f'<Query({self._definition})>'

def toregex(wildcard):
    pass

def convert(filters):
    """Convert filters to the mongo query syntax.
    A special care is taken to handle old-style negative filters correctly
    """
    pass

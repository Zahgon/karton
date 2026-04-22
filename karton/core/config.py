import configparser
import os
import re
import warnings
from typing import Any, Dict, List, Optional, cast, overload

class Config(object):
    """
    Simple config loader.

    Loads configuration from paths specified below (in provided order):

    - ``/etc/karton/karton.ini`` (global)
    - ``~/.config/karton/karton.ini`` (user local)
    - ``./karton.ini`` (subsystem local)
    - path from ``KARTON_CONFIG_FILE`` environment variable
    - ``<path>`` optional, additional path provided in arguments

    It is also possible to pass configuration via environment variables.
    Any variable named KARTON_FOO_BAR is equivalent to setting 'bar' variable
    in section 'foo' (note the lowercase names).

    Environment variables have higher precedence than those loaded from files.

    :param path: Path to additional configuration file
    :param check_sections: Check if sections ``redis`` and ``s3`` are defined
        in the configuration
    """
    SEARCH_PATHS = ['/etc/karton/karton.ini', os.path.expanduser('~/.config/karton/karton.ini'), './karton.ini']

    def __init__(self, path: Optional[str]=None, check_sections: Optional[bool]=True) -> None:
        self._config: Dict[str, Dict[str, Any]] = {}
        path_from_env = os.getenv('KARTON_CONFIG_FILE')
        if path_from_env:
            if not os.path.isfile(path_from_env):
                raise IOError(f'Configuration file not found in {path_from_env}')
            self.SEARCH_PATHS = self.SEARCH_PATHS + [path_from_env]
        if path is not None:
            if not os.path.isfile(path):
                raise IOError('Configuration file not found in ' + path)
            self.SEARCH_PATHS = self.SEARCH_PATHS + [path]
        self._load_from_file(self.SEARCH_PATHS)
        self._load_from_env()
        if check_sections:
            if self.has_section('minio') and (not self.has_section('s3')):
                self._map_minio_to_s3()
            if not self.has_section('s3'):
                raise RuntimeError('Missing S3 configuration')
            if not self.has_section('redis'):
                raise RuntimeError('Missing Redis configuration')

    def _map_minio_to_s3(self):
        """
        Configuration backwards compatibility. Before 5.x.x [minio] section was used.
        """
        pass

    def set(self, section_name: str, option_name: str, value: Any) -> None:
        """
        Sets value in configuration
        """
        pass

    def get(self, section_name: str, option_name: str, fallback: Optional[Any]=None) -> Any:
        """
        Gets value from configuration or returns ``fallback`` (None by default)
        if value was not set.
        """
        pass

    def has_section(self, section_name: str) -> bool:
        """
        Checks if configuration section exists
        """
        pass

    def has_option(self, section_name: str, option_name: str) -> bool:
        """
        Checks if configuration value is set
        """
        pass

    @overload
    def getint(self, section_name: str, option_name: str, fallback: int) -> int:
        pass

    @overload
    def getint(self, section_name: str, option_name: str) -> Optional[int]:
        pass

    @overload
    def getint(self, section_name: str, option_name: str, fallback: Optional[int]) -> Optional[int]:
        pass

    def getint(self, section_name: str, option_name: str, fallback: Optional[int]=None) -> Optional[int]:
        """
        Gets value from configuration or returns ``fallback`` (None by default)
        if value was not set. Value is coerced to int type.
        """
        pass

    @overload
    def getboolean(self, section_name: str, option_name: str, fallback: bool) -> bool:
        pass

    @overload
    def getboolean(self, section_name: str, option_name: str) -> Optional[bool]:
        pass

    def getboolean(self, section_name: str, option_name: str, fallback: Optional[bool]=None) -> Optional[bool]:
        """
        Gets value from configuration or returns ``fallback`` (None by default)
        if value was not set. Value is coerced to bool type.

        .. seealso::

           https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.getboolean
        """
        pass

    def append_to_list(self, section_name: str, option_name: str, value: Any) -> None:
        """
        Appends value to a list in configuration
        """
        pass

    def load_from_dict(self, data: Dict[str, Dict[str, Any]]) -> None:
        """
        Updates configuration values from dictionary compatible with
        ``ConfigParser.read_dict``. Accepts value in native type, so you
        don't need to convert them to string.

        None values are treated like missing value and are not added.

        .. code-block:: json

            {
               "section-name": {
                   "option-name": "value"
               }
            }

        """
        pass

    def _load_from_file(self, paths: List[str]) -> None:
        """
        Function used for loading configuration items from karton.ini files

        :meta private:
        """
        pass

    def _load_from_env(self) -> None:
        """
        Function used for loading configuration items from the environment variables

        :meta private:
        """
        pass

    def __getitem__(self, section) -> Dict[str, Any]:
        """Gets a section named `section` from the config"""
        return self._config[section]

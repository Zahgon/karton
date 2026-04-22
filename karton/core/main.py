import argparse
import logging
import os.path
from configparser import ConfigParser
from typing import Any, Dict, List
import boto3
from redis import StrictRedis
from .__version__ import __version__
from .backend import KartonBackend
from .config import Config
from .karton import Consumer, LogConsumer
log = logging.getLogger(__name__)

class CliLogger(LogConsumer):
    identity = 'karton.cli-logger'

    def process_log(self, event: Dict[str, Any]) -> Any:
        pass

def get_user_option(prompt: str, default: str) -> str:
    pass

def configuration_wizard(config_filename: str) -> None:
    pass

def print_bind_list(config: Config, output_format: str) -> None:
    pass

def delete_bind(config: Config, karton_name: str) -> None:
    pass

def main() -> None:
    pass

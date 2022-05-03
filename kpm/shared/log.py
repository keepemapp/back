import json
import logging.config
import os
import pathlib
import sys
from typing import Any, Dict, Union

from kpm.settings import settings as s


class JsonLogger:
    def __init__(self):
        # Disable verbosity of existing loggers
        for _, logger in logging.root.manager.loggerDict.items():
            logger.setLevel(logging.ERROR)

        if s.ENVIRONMENT != 'prod':
            self._log = logging.getLogger(f"kpm-{s.ENVIRONMENT}")
        else:
            self._log = logging.getLogger("kpm")
        self._log.setLevel(s.LOG_LEVEL)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(s.LOG_LEVEL)
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", %(message)s, "app_name": "%(name)s"}'
        )
        ch.setFormatter(formatter)
        self._log.addHandler(ch)
        self._log.info("Starting logger")

    @staticmethod
    def _parse_msg(msg: Union[Dict, str, Any], component):

        if isinstance(msg, dict):
            msg["component"] = component
            dic = msg
        else:
            dic = {"component": component, "message": msg}
        return json.dumps(dic)[1:-1]

    def info(self, msg: Union[Dict, str, Any], component="na"):
        self._log.info(self._parse_msg(msg, component))

    def debug(self, msg: Union[Dict, str, Any], component="na"):
        self._log.debug(self._parse_msg(msg, component))

    def error(self, msg: Union[Dict, str, Any], component="na"):
        self._log.error(self._parse_msg(msg, component))

    def exception(self, msg: Union[Dict, str, Any], component="na"):
        self._log.exception(self._parse_msg(msg, component))

    def warning(self, msg: Union[Dict, str, Any], component="na"):
        self._log.warning(self._parse_msg(msg, component))

    def critical(self, msg: Union[Dict, str, Any], component="na"):
        self._log.critical(self._parse_msg(msg, component))


logger = JsonLogger()

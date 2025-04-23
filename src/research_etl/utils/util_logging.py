import logging
import os
import time
import uuid
import traceback
from typing import Any, Dict, Union, Optional

MdValues = Optional[Union[str, int, float]]


class ProcessLogger:
    """
    Class to help with logging events that happen inside of a function.
    """

    # default_data keys that can not be added as metadata
    protected_keys = [
        "parent",
        "process_name",
        "process_id",
        "uuid",
        "status",
        "duration",
        "error_type",
    ]

    def __init__(self, process_name: str, auto_start: bool = True, **metadata: MdValues) -> None:
        """
        reate a process logger with a name and optional metadata.

        :param process: name of process being logged
        :param auto_start: bool -> if True(default) automatically start log
        :param metadata: any key/value pair to log
        """
        logging.getLogger().setLevel("INFO")

        self.default_data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

        self.default_data["parent"] = os.environ.get("SERVICE_NAME", "unknown")
        self.default_data["process_name"] = process_name

        self.start_time = 0.0
        self.uuid = ""

        self.add_metadata(**metadata)

        if auto_start:
            self.start()

    def _get_log_string(self) -> str:
        """create logging string for log write"""
        logging_list = []
        # add default data to log output
        logging_list.append(f"uuid={self.uuid}")
        for key, value in self.default_data.items():
            logging_list.append(f"{key}={value}")

        # add metadata to log output
        for key, value in self.metadata.items():
            logging_list.append(f"{key}={value}")

        return ", ".join(logging_list)

    def add_metadata(self, **metadata: MdValues) -> None:
        """add metadata to the process logger"""
        for key, value in metadata.items():
            # skip metadata key if protected as default_data key
            # maybe raise on this? instead of fail silently
            if key in ProcessLogger.protected_keys:
                continue
            self.metadata[str(key)] = str(value)

    def start(self) -> None:
        """log the start of a proccess"""
        self.uuid = str(uuid.uuid4())
        self.default_data["process_id"] = os.getpid()
        self.default_data["status"] = "started"
        self.default_data.pop("duration", None)
        self.default_data.pop("error_type", None)

        self.start_time = time.monotonic()

        logging.info(self._get_log_string())

    def log_complete(self, **metadata: MdValues) -> None:
        """
        Log completion of a proccess.

        :param metadata: any key/value pair to log
        """
        self.add_metadata(print_log=False, **metadata)

        duration = time.monotonic() - self.start_time
        self.default_data["status"] = "complete"
        self.default_data["duration"] = f"{duration:.2f}"

        logging.info(self._get_log_string())

    def log_failure(self, exception: Exception) -> None:
        """log the failure of a process with exception type"""
        duration = time.monotonic() - self.start_time
        self.default_data["status"] = "failed"
        self.default_data["duration"] = f"{duration:.2f}"
        self.default_data["error_type"] = type(exception).__name__

        # This is for exceptions that are not 'raised'
        # 'raised' exceptions will also be logged to sys.stderr
        for tb in traceback.format_tb(exception.__traceback__):
            for line in tb.strip("\n").split("\n"):
                p_line = line.strip("\n")
                tb_line = f"uuid={self.uuid}, {p_line}"
                logging.error(tb_line)

        # Log Exception
        for line in traceback.format_exception_only(exception):
            p_line = line.strip("\n")
            except_line = f"uuid={self.uuid}, {p_line}"
            logging.error(except_line)

        # Log Process Failure
        logging.info(self._get_log_string())

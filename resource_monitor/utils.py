"""
    Root resource/event loggers.
    Decorator and context manager for event logging.
"""
from multiprocessing import Process, Pipe, Event
from atexit import register
from os import getpid
from typing import Optional, Union, Sequence, Dict
from .resource_logger import ResourceLogger
from .event_logger import EventLogger


RESOURCE_LOGGING_SUBPROCESS = None
RESOURCE_LOGGING_STOP_EVENT = Event()


def resource_logging_worker(
    pid: Union[int, Sequence[int]],
    write_pipe,
    output_file: Optional[str] = None,
    interval: float = 1.0,
    gpu_ids: Optional[Union[int, Sequence[int]]] = None,
    stop_event: Optional["Event"] = None
):
    """ The worker function in the resource monitor subprocess. """
    logger = ResourceLogger(pid, output_file, interval, gpu_ids, stop_event)
    write_pipe.send("kick off")
    logger.run()
    logger.clean_up()


def setup_root_resource_logger(
    output_file: Optional[str] = None,
    interval: float = 1.0,
    gpu_ids: Optional[Union[int, Sequence[int]]] = None,
):
    """
        Initialize the root resource logger to monitor current process.
        See the docs of ResourceLogger.
    """
    global RESOURCE_LOGGING_SUBPROCESS, RESOURCE_LOGGING_STOP_EVENT

    pid = getpid()
    if output_file is None:
        output_file = f"resource_monitor_PID{pid}.log"

    read_pipe, write_pipe = Pipe(False)

    monitor_process = Process(
        target=resource_logging_worker,
        args=[pid, write_pipe, output_file, interval, gpu_ids, RESOURCE_LOGGING_STOP_EVENT]
    )
    monitor_process.start()
    _ = read_pipe.recv()
    RESOURCE_LOGGING_SUBPROCESS = monitor_process


EVENT_LOGGER = None


def setup_root_event_logger(output_file: Optional[str] = None):
    """
        Initialize the root event logger to monitor current process.
        See the docs of EventLogger.
    """
    pid = getpid()
    if output_file is None:
        output_file = f"event_monitor_PID{pid}.log"
    global EVENT_LOGGER
    EVENT_LOGGER = EventLogger(output_file)


def get_root_event_logger():
    """" If the event logger is not initialized, use default arguments to initialize it. """
    global EVENT_LOGGER
    if EVENT_LOGGER is None:
        setup_root_event_logger()
    return EVENT_LOGGER


def monitor_function(
    event_logger: Optional[EventLogger] = None, function_name: Optional[str] = None
):
    """
        Monitor the calling/returning of the wrapped function.
        The default event name is the function name.
    """
    def monitorit_wrapper(func):
        nonlocal event_logger, function_name, function_name
        if function_name is None:
            function_name = func.__name__

        call_counter = 0

        def func_wrapper(*args, **kwargs):
            nonlocal event_logger, function_name, call_counter
            if event_logger is None:
                event_logger = get_root_event_logger()
            else:
                assert isinstance(event_logger, EventLogger)
            call_counter += 1
            event_logger.log_start(function_name, call_counter)
            results = func(*args, **kwargs)
            event_logger.log_end(function_name, call_counter)
            return results

        return func_wrapper

    return monitorit_wrapper


class MonitorRegion:
    """
        Monitor the code inside a with-statement block.
    """
    counter: Dict[str, int] = {}

    def __init__(
        self, region_name: str, event_logger: Optional[EventLogger] = None
    ) -> None:
        self.event_logger = (
            get_root_event_logger() if event_logger is None else event_logger
        )
        self.region_name = region_name
        if self.region_name in MonitorRegion.counter:
            MonitorRegion.counter[self.region_name] += 1
        else:
            MonitorRegion.counter[self.region_name] = 1

    def __enter__(self):
        self.event_logger.log_start(self.region_name, MonitorRegion.counter[self.region_name])

    def __exit__(self, *_):
        self.event_logger.log_end(self.region_name, MonitorRegion.counter[self.region_name])


def monitor_region(region_name, event_logger=None):
    """ return a new MonitorRegion context manager """
    return MonitorRegion(region_name, event_logger)


@register
def clean_up():
    """"clean up root loggers if initialized """
    global EVENT_LOGGER, RESOURCE_LOGGING_SUBPROCESS
    if EVENT_LOGGER is not None:
        EVENT_LOGGER.clean_up()
    if RESOURCE_LOGGING_STOP_EVENT is not None:
        RESOURCE_LOGGING_STOP_EVENT.set()
    if RESOURCE_LOGGING_SUBPROCESS is not None:
        RESOURCE_LOGGING_SUBPROCESS.terminate()

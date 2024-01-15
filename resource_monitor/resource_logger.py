"""
    ResourceLogger class
"""
from threading import Event
from time import sleep, perf_counter
from typing import List, Optional, Sequence, Union
from sys import stdout
from os import getpid

import psutil  # type: ignore


MEGABYTE = 1024**2
GIGABYTE = 1024**3


class ResourceLogger:
    """
    Log the total cpu utilization/memory usage/io counts/gpu memory usage of processes.

    ResourceLogger.run() should be running in a separete process,
        wake at a certain frequency to record system resource usage.
    The results will be written to a file in CSV format.

    TODO: document what resource will be monitored.

    """
    RESOURCE_LOGGING_LATENCY = 0.01

    def __init__(
        self,
        pid: Optional[Union[int, Sequence[int]]] = None,
        output: Optional[str] = None,
        interval: float = 1.0,
        gpu_ids: Optional[Union[int, Sequence[int]]] = None,
        stop_event: Optional[Event] = None,
    ) -> None:
        """
        Args:
            pid (Optional[Union[int, Sequence[int]]], optional):
                PID of the processes to monitor. Defaults to None.
            output (Optional[Union[str, TextIO]], optional):
                Output file. The results are appended to the file. Defaults to None.
            interval (float, optional):
                Time interval (seconds) between recording.
                __init__() will try to estimate the logging latency on current machine.
                `interval` needs to be 2x longer than it.
                Defaults to 1.0.
            gpu_ids (Optional[Union[int, Sequence[int]]], optional):
                GPU indices to monitor. Requires `pynvml`. Defaults to None.
        """
        if pid is None:
            pid = [getpid()]
        elif isinstance(pid, int):
            pid = [pid]
        else:
            pid = list(pid)
        self.pids: List[int] = pid

        if output is None:
            self.output = stdout
        else:
            self.output = open(output, "w", encoding="utf-8")

        self.stop_event: Optional[Event] = stop_event

        assert interval >= 0.
        self.interval: float = interval

        if gpu_ids is None:
            gpu_ids = []
        elif isinstance(gpu_ids, int):
            gpu_ids = [gpu_ids]
        else:
            gpu_ids = list(gpu_ids)
        self.gpu_ids: List[int] = gpu_ids

        self.gpu_logger: Optional["GpuLogger"]
        if len(self.gpu_ids) > 0:
            # GpuLogger requires module `pynvml`
            from .gpu_logger import GpuLogger
            self.gpu_logger = GpuLogger(self.pids, self.gpu_ids)
        else:
            self.gpu_logger = None

        # benchmark the latency of resource logging
        processes = [psutil.Process(pid) for pid in self.pids]
        start = perf_counter()
        for _ in range(8):
            __ = self.get_resource_info(processes)
        end = perf_counter()
        ResourceLogger.RESOURCE_LOGGING_LATENCY = (end - start)/8
        self.output.write(
            "In current environment, the latency of resource logging is estimated to be "
            f"{ResourceLogger.RESOURCE_LOGGING_LATENCY:.4e} s, "
            "your interval is advised to be 2x greater than it.\n"
        )
        assert self.interval >= 2 * ResourceLogger.RESOURCE_LOGGING_LATENCY, \
            f"estimated resource logging latency: {ResourceLogger.RESOURCE_LOGGING_LATENCY:.4e} s"

        # log global resource information
        global_info = []
        global_info.append(f"logger_process_pid:{getpid()}")
        global_info.append(f"cpu_count:{psutil.cpu_count(logical=False)}")
        virtual_memory = psutil.virtual_memory()
        global_info.append(f"vm_total_mb:{virtual_memory.total//MEGABYTE}")
        global_info.append(f"vm_available_mb:{virtual_memory.available//MEGABYTE}")
        swap_memory = psutil.swap_memory()
        global_info.append(f"swap_total_mb:{swap_memory.total//MEGABYTE}")
        global_info.append(f"swap_free_mb:{swap_memory.free//MEGABYTE}")
        # TODO: add disk information
        # TODO: add network information
        if self.gpu_logger is not None:
            for gpu_id, total, free in zip(
                self.gpu_ids, self.gpu_logger.get_total(), self.gpu_logger.get_free()
            ):
                global_info.append(f"gpu_{gpu_id}_total_mb:{total//MEGABYTE}")
                global_info.append(f"gpu_{gpu_id}_free_mb:{free//MEGABYTE}")
        self.output.write(",".join(global_info) + "\n")

        # log the header of the table
        # all numbers are resource consumption numbers, global means that of all processes
        headers = [
            "time",
            "cpu_percent",
            "cpu_percent_global",
            "rss_mb",
            "vms_mb",
            "vms_global_mb",
            "swap_used_mb",
            "read_count",
            "read_count_global",
            "read_mb",
            "read_mb_global",
            "write_count",
            "write_count_global",
            "write_mb",
            "write_mb_global"
        ]
        if self.gpu_logger is not None:
            for i in self.gpu_ids:
                headers.extend([f"gpu_{i}_mem_mb", f"gpu_{i}_mem_mb_global"])
        self.output.write(",".join(headers) + "\n")

        self.output.flush()

    def get_resource_info(self, processes: List[psutil.Process]) -> Optional[List[Union[int, float]]]:
        """" get the resource info """
        # TODO: options to dynamically include the subprocesses
        active_processes = []
        for p in processes:
            try:
                if p.status() not in (
                    psutil.STATUS_STOPPED,
                    psutil.STATUS_DEAD,
                    psutil.STATUS_ZOMBIE,
                ):
                    active_processes.append(p)
            except psutil.NoSuchProcess:
                continue

        processes = active_processes
        if len(processes) == 0:
            return None

        process_infos = [p.as_dict(attrs=["cpu_percent", "memory_info", "io_counters"]) for p in processes]

        numbers = []
        numbers.append(perf_counter())  # time
        numbers.append(sum(p["cpu_percent"] for p in process_infos))  # cpu_percent
        numbers.append(psutil.cpu_percent())  # cpu_percent_global
        numbers.append(
            sum(p["memory_info"].rss // MEGABYTE for p in process_infos)
        )  # rss_mb
        numbers.append(
            sum(p["memory_info"].vms // MEGABYTE for p in process_infos)
        )  # vms_mb
        numbers.append(
            psutil.virtual_memory().used // MEGABYTE
        )  # vms_global_mb
        numbers.append(psutil.swap_memory().used // MEGABYTE)  # swap_used_mb
        global_io_counter = psutil.disk_io_counters()
        numbers.append(
            sum(p["io_counters"].read_count for p in process_infos)
        )  # read_count
        numbers.append(global_io_counter.read_count)  # read_count_global
        numbers.append(
            sum(p["io_counters"].read_bytes // MEGABYTE for p in process_infos)
        )  # read_mb
        numbers.append(global_io_counter.read_bytes // MEGABYTE)  # read_mb_global
        numbers.append(
            sum(p["io_counters"].write_count for p in process_infos)
        )  # write_count
        numbers.append(global_io_counter.write_count)  # write_count_global
        numbers.append(
            sum(p["io_counters"].write_bytes // MEGABYTE for p in process_infos)
        )  # write_mb
        numbers.append(global_io_counter.write_bytes // MEGABYTE)  # write_mb_global
        if self.gpu_logger is not None:
            for process_used, global_used in zip(
                self.gpu_logger.get_process_used(), self.gpu_logger.get_used()
            ):
                numbers.extend(
                    [process_used // MEGABYTE, global_used // MEGABYTE]
                )  # "gpu_{i}_mem_mb", f"gpu_{i}_mem_mb_global"

        return numbers

    def run(self) -> None:
        """
            Start monitoring. It runs util all the processes stop running.
        """
        processes = [psutil.Process(pid) for pid in self.pids]
        while True:
            sleep(self.interval - ResourceLogger.RESOURCE_LOGGING_LATENCY)
            numbers = self.get_resource_info(processes)
            if numbers is None:
                break
            if self.stop_event is not None and self.stop_event.is_set():
                break
            row = ",".join([str(n) for n in numbers])
            self.output.write(row + '\n')
            self.output.flush()

    def clean_up(self) -> None:
        """ close file handle """
        if self.output is not stdout:
            self.output.close()

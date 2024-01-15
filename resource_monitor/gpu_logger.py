""" GPU Resource Logger """
from typing import Sequence, List

from pynvml import ( # type: ignore
    nvmlInit, nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo, nvmlDeviceGetComputeRunningProcesses
)


class GpuLogger:
    """GPU Resource Logger. Currently on GPU memory usage is monitored."""

    def __init__(self, pids: Sequence[int], gpu_ids: Sequence[int]) -> None:
        """
        Args:
            pids (Sequence[int]): PID of the processes to monitor
            gpu_ids (Sequence[int]): indices of the GPUs to monitor
        """
        nvmlInit()
        self.pids = pids
        self.handles = [nvmlDeviceGetHandleByIndex(i) for i in gpu_ids]

    @property
    def num_gpus(self) -> int:
        """ the number of GPUs under monitoring """
        return len(self.handles)

    @property
    def num_processes(self) -> int:
        """ the number of processes under monitoring """
        return len(self.pids)

    def set_pids(self, pids) -> None:
        """ update the PID of the processes to monitor """
        self.pids = pids

    def get_total(self) -> List[int]:
        """ get total memory of each GPU in bytes """
        return [nvmlDeviceGetMemoryInfo(h).total for h in self.handles]

    def get_used(self) -> List[int]:
        """ get used memory of each GPU in bytes """
        return [nvmlDeviceGetMemoryInfo(h).used for h in self.handles]

    def get_free(self) -> List[int]:
        """ get free memory of each GPU in bytes """
        return [nvmlDeviceGetMemoryInfo(h).free for h in self.handles]

    def get_process_used(self) -> List[int]:
        """ get used memory (by the processes under monitoring) of each GPU in bytes """
        # TODO: it seems on Windows process-wise memory usage query always returns 0.
        gpu_processes = [nvmlDeviceGetComputeRunningProcesses(h) for h in self.handles]
        gpu_used_mem = [
            sum(
                p.usedGpuMemory
                for p in processes
                if p.pid in self.pids and p.usedGpuMemory is not None
            )
            for processes in gpu_processes
        ]
        return gpu_used_mem

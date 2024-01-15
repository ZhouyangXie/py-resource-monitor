""" Example of using root resource logger and event logger """
from os import remove
from time import perf_counter, sleep

import numpy as np

from resource_monitor import (
    monitor_function,
    monitor_region,
    setup_root_event_logger,
    setup_root_resource_logger,
)


# log the calling/returning of the function by monitor_function() decorator
@monitor_function()
def my_func(gpu_id):
    """ example function to use CPU/GPU and write/read files """
    s = perf_counter()
    for _ in range(10):
        sleep(0.5)
        a = np.random.rand(1 * 1024 * 1024)
        if gpu_id is not None:
            import torch
            b = torch.tensor(a, device=f"cuda:{gpu_id}")
        np.save("tmp.npy", a)
        # monitor the entrance/exit of a code region by monitor_region(event_name: str)
        with monitor_region("load numpy array"):
            _ = np.load("tmp.npy")
        if gpu_id is not None:
            b.to("cpu")
    remove("tmp.npy")
    print(f"elapse(s): { perf_counter() - s:.4f}",)


if __name__ == "__main__":
    # `setup_root_resource_logger()` starts a subprocess,
    # so it must not be called in the bootstraping phase (module initialization stage) of Python,
    setup_root_resource_logger(output_file="my_func_resource.log", interval=0.1, gpu_ids=None)

    # the latency of event logger is about 0.02ms, make sure your events do not happen too frequently/fast
    setup_root_event_logger("my_func_event.log")

    # if this system is CUDA device enabled, run:
    # my_func(0)
    # else, run:
    my_func(None)

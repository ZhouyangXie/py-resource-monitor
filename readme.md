### What's This

This Python package helps you monitoring system resource of any process and profiling Python functions/code-blocks together.

Existing profiling tools do not fully monitor system resource usage like CPU utilization/memory usage/disk IO etc., while existing process monitoring tools do not dive into codes. This package's goal is to enable a line-by-line inspection on system resource usage.

Currently, the latency of resource usage monitoring is not low enough (~0.3ms on Linux). So this package is suitable for high latency functions only, such as read/write of large files, deep learning model training/inference, image/video processing etc.

See "What's Monitored" for details.

### How to Install

Download a `.zip` package from this repo and just `pip install` it.

Dependencies:
* Python >= 3.7
* psutil >= 5.3.0
* numpy

Optional dependencies:
* pynvml (if you want to monitor NVidia GPU)
* matplotlib (to run `print_report.py`)
* pytorch (to run `example.py` with GPU).

### How to Use
#### To Monitor Processes
"""sh
usage: __main__.py [-h] --pid PID [--output OUTPUT] [--gpu_ids GPU_IDS] [--interval INTERVAL]

optional arguments:
  -h, --help           show this help message and exit
  --pid PID            Process PID separated by comma, like "1,2,3"
  --output OUTPUT      Output file. If not provided, output to stdout.
  --gpu_ids GPU_IDS    GPU indices to monitor. If not provided, do not monitor GPUs.
  --interval INTERVAL  Time interval (second) between recording. Defaults to 1.0
"""

For example, to monitor running processes PID 1234 and 4321 with GPU utility on GPU 0-3 and output the result to resources.log:

"""sh
python -m resource_monitor --pid 1234,4321 --gpus 0,1,2,3 --output resources.log
"""

The monitor process finishes when process 1234 and 4321 are all finished, or stopped manually by Ctrl+C/Z.

The recorded resource usage will be the sum of all monitored processes.

#### To Monitor Python Code
See `example.py`. It's well-commented and simple enough.

Then, run `example.py`, two log files will be generated. It contains time-series information about your monitored events and resources.

Last, see `print_report.py`(simple, too) and run it. It will print and plot what's recorded in the logs:
* Print the mean duration of the monitored functions & code-blocks.
* Print the system resource overview.
* Plot the time v.s. resource-usage curves in a `.png` image.

### What's Monitored

If you have done the steps in "How to Use", you can see what's monitored.

In resource log:
* time: the time point of recording.
* cpu_percent: CPU utilization of the monitored process in percent.
* cpu_percent_global: overall CPU utilization in percent.
* rss_mb: physical memory usage of the monitored process that is not swapped to disk in MB.
* vms_mb: virtual memory usage (rss and swapped) of the monitored process in MB.
* vms_global_mb: overall virtual memory usage in MB.
* swap_used_mb: overall swap memory usage in MB.
* read_count: cumulative count of disk read of the monitored process.
* read_count_global: cumulative count of overall disk read.
* read_mb: cumulative size data read from disk of the monitored process in MB.
* read_mb_global: cumulative overall size data read from disk in MB.
* write_count: cumulative count of disk write of the monitored process.
* write_count_global: cumulative count of overall disk write.
* write_mb: cumulative size data written to disk of the monitored process in MB.
* write_mb_global: cumulative overall size data written to disk in MB.
The system resource overview is recorded at the start of the resource log.

In event log, the entrance & exit time of the code block or function is recorded. Note that each entrance is identified by a counter (the last column), so recursive calls are not confused.

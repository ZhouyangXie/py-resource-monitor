""" Commandline interface to start a resource logger """
import argparse

from .resource_logger import ResourceLogger


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pid", type=str, required=True, help="Process PID separated by comma, like \"1,2,3\"")
    parser.add_argument(
        "--output", type=str, required=False, default="",
        help="Output file. If not provided, output to stdout."
    )
    parser.add_argument(
        "--gpu_ids", type=str, required=False, default="",
        help="GPU indices to monitor. If not provided, do not monitor GPUs."
    )
    parser.add_argument(
        "--interval", type=float, required=False, default=1.0,
        help="Time interval (second) between recording. Defaults to 1.0"
    )
    args = parser.parse_args()
    pids = [int(pid) for pid in args.pid.split(",")]
    output = args.output if len(args.output) > 0 else None
    interval = args.interval
    assert interval > 0
    gpu_ids = [int(i) for i in args.gpu_ids.split(",")] if len(args.gpu_ids) > 0 else []
    ResourceLogger(pid=pids, output=output, interval=args.interval, gpu_ids=gpu_ids).run()

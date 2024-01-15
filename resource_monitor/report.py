"""
    Merge the logs of EventLogger and ResourceLogger,
    and report a event-wise resource monitoring result.
"""
from typing import Dict, List, Tuple
import numpy as np
from numpy.typing import NDArray


def parse_event_log(filename: str) -> Dict[str, NDArray[np.float64]]:
    """parse the event log to a dict of event name to the start/end times of different event id

    Args:
        filename (str): event log file path

    Returns:
        Dict[str, NDArray[np.float64]]:
            event name and a 2-dim ndarray (shape=(n_occurrences, 2)) indicating the start/finish time
    """
    with open(filename, mode="r", encoding="utf-8") as f:
        records = f.readlines()

    event_intervals: Dict[str, Dict[str, List[float]]] = {}
    for record in records:
        record = record.strip("\n")
        time, start, event_name, event_id = record.split(",")
        if event_name not in event_intervals:
            event_intervals[event_name] = {}
        if event_id not in event_intervals[event_name]:
            event_intervals[event_name][event_id] = [0., 0.]

        if start == "start":
            event_intervals[event_name][event_id][0] = float(time)
        else:
            event_intervals[event_name][event_id][1] = float(time)

    return dict((k, np.array(list(v.values()))) for k, v in event_intervals.items())


def parse_resource_log(
    filename: str,
) -> Tuple[Dict[str, int], Dict[str, NDArray]]:
    """parse the event log to a dict of global information and a dict of resource usage

    Args:
        filename (str): resource log file path

    Returns:
        Tuple[Dict[str, int], Dict[str, NDArray]]:
            The first dict is the global resource information.
                See ResourceLogger or the 1-st row of the log file.
            The second dict is the process-specific resource information,
                mapping resource name (str) or logging time to a 1-D int64/float64 NDarray (same length).
                See ResourceLogger or the 2-nd row of the log file.
    """
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    global_info_line = lines[1].strip("\n")
    global_info = dict(
        (g.split(":")[0], int(g.split(":")[1])) for g in global_info_line.split(",")
    )

    headers = lines[2].strip("\n").split(",")
    records = np.fromstring(",".join(lines[3:]), sep=",", dtype=np.float64).reshape(
        (-1, len(headers))
    )
    resource_usage = {}
    for i, header in enumerate(headers):
        if header in ("time", "cpu_percent", "cpu_percent_global"):
            resource_usage[header] = records[:, i].astype(np.float64)
        else:
            resource_usage[header] = records[:, i].astype(np.int64)

    return global_info, resource_usage

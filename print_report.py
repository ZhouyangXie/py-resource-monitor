""" print and visualize the logs produced by exapmle.py """
import matplotlib.pyplot as plt  # type: ignore

from resource_monitor.report import parse_event_log, parse_resource_log


if __name__ == "__main__":
    # parse the event log
    event_times = parse_event_log("my_func_event.log")
    for k, times in event_times.items():
        # `times` is a np.ndarray shape=(N,2) dtype=np.float64,
        # meaning the start/end time points of the event
        mean_elapse = (times[:, 1] - times[:, 0]).mean().item()
        # print the mean duration of the events (mean among occurrences identified by the counter)
        print(f"event: {k}, mean elapse: {mean_elapse:.4e} s")

    # parse the resource log
    global_info, resource_usage = parse_resource_log("my_func_resource.log")
    print("machine resource information:")
    for k, v in global_info.items():
        print(k, ": ", v)

    # extract the time column
    times = resource_usage["time"]
    del resource_usage["time"]

    # plot each of the resource and save
    fig = plt.figure(figsize=(5 * len(resource_usage), 5), facecolor="w")
    axes = fig.subplots(ncols=len(resource_usage), nrows=1)
    for i, (resource_name, usage) in enumerate(resource_usage.items()):
        print(resource_name, " peak: ", usage.max(), " average: ", usage.mean(), )
        ax = axes[i]
        ax.set_title(resource_name + " usage")
        ax.set_xlabel("time(s)")
        if "percent" in resource_name:
            ax.set_ylabel("percent(%)")
        ax.plot(times, usage)
        ax.grid()

    plt.savefig("resource_usage.png", bbox_inches='tight', dpi=300)

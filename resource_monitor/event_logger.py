"""
    Event loggers record the start/end of lasting events,
    like function calling & returning, file opening & closing.
"""
from typing import Optional, TextIO, Union
from time import perf_counter
from sys import stdout


class EventLogger:
    """ Event logger """
    def __init__(self, output: Optional[Union[str, TextIO]] = None) -> None:
        self.output: Optional[Union[str, TextIO]] = output

    def log_start(self, event_name: str, event_id: Optional[Union[int, str]] = None) -> None:
        """ log the start of an event """
        if self.output is None:
            self.output = stdout
        elif isinstance(self.output, str):
            self.output = open(self.output, "w", encoding="utf-8")

        assert "," not in event_name, f"got {event_name}"
        event_id = "" if event_id is None else str(event_id)
        self.output.write(f"{perf_counter()},start,{event_name},{event_id}\n")

    def log_end(self, event_name: str, event_id: Optional[Union[int, str]] = None) -> None:
        """ log the end of an event, the event start must previously be logged. """
        assert self.output is not None and not isinstance(self.output, str)
        assert "," not in event_name, f"got {event_name}"
        event_id = "" if event_id is None else str(event_id)
        self.output.write(f"{perf_counter()},end,{event_name},{event_id}\n")

    def clean_up(self) -> None:
        """ close the file handle """
        assert self.output is not None and not isinstance(self.output, str)
        if self.output is not stdout:
            self.output.close()

"""Misc utils."""

import re
from datetime import datetime


def timestamp_format(
    timestamp_timezone: str, format: str = "%a %b %d %H:%M:%S %Y"
) -> str:
    """Convert a string containing a timestamp and maybe timezone to given format.

    Note
    -----
    The default ``format`` is the same as the default format used by git.

    """
    split = timestamp_timezone.split()
    date_time = datetime.fromtimestamp(int(split[0])).strftime(format)
    return f"{date_time} {split[1]}" if len(split) == 2 else date_time


def timestamp_modify(data: str) -> str:
    """Modify the timestamp"""
    match = re.search("(?P<who>.*<.*>) (?P<date>.*)", data)
    if match:
        return f"{match.group('who')}\n" f"{timestamp_format(match.group('date'))}"
    return data

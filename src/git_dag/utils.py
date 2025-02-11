"""Misc utils."""

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

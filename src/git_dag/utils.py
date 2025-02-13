"""Misc utils."""

import re
from datetime import datetime


def transform_ascii_control_chars(text: str) -> str:
    """Transform ascii control characters.

    Note
    -----
    This is necessary because SVGs exported from graphviz cannot be displayed when they
    contain certain ascii control characters.

    """

    def ascii_to_caret_notation(match):
        char = match.group(0)
        return f"^{chr(ord(char) + 64)}"

    # do not transform \a \b \t \n \v \f \r (which correspond to ^G-^M)
    # https://en.wikipedia.org/wiki/ASCII#Control_code_table
    return re.sub(r"[\x01-\x06\x0E-\x1A]", ascii_to_caret_notation, text)


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

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

    def ascii_to_caret_notation(match: re.Match[str]) -> str:
        char = match.group(0)
        return f"^{chr(ord(char) + 64)}"

    # do not transform \a \b \t \n \v \f \r (which correspond to ^G-^M)
    # https://en.wikipedia.org/wiki/ASCII#Control_code_table
    return re.sub(r"[\x01-\x06\x0E-\x1A]", ascii_to_caret_notation, text)


def timestamp_format(data: str, fmt: str = "%a %b %d %H:%M:%S %Y") -> str:
    """Format a timestamp.

    Note
    -----
    The default format (``fmt``) is the same as the default format used by git.

    """

    def formatter(timestamp_timezone: str) -> str:
        """Convert a string containing a timestamp and maybe a timezone."""
        split = timestamp_timezone.split()
        date_time = datetime.fromtimestamp(int(split[0])).strftime(fmt)
        return f"{date_time} {split[1]}" if len(split) == 2 else date_time

    match = re.search("(?P<who>.*<.*>) (?P<date>.*)", data)
    if match:
        return f"{match.group('who')}\n" f"{formatter(match.group('date'))}"
    return data

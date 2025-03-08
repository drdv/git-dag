"""Misc utils."""

import codecs
import re
from datetime import datetime


def escape_decode(text: str) -> str:
    """Decode escapes of escapes (e.g., ``\\\\n -> \\n``).

    Note
    -----
    The approach in https://stackoverflow.com/a/37059682 is used because it handles
    unicode characters. FIXME: unfortunately, it relies on the internal function
    ``codecs.escape_decode`` (https://github.com/python/cpython/issues/74773).

    """
    return codecs.escape_decode(text.encode())[0].decode()  # type: ignore


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


def creator_timestamp_format(
    data: str, fmt: str = "%a %b %d %H:%M:%S %Y"
) -> tuple[str, str, str]:
    """Format a creator (author/committer) and timestamp.

    Note
    -----
    The default format (``fmt``) is the same as the default format used by git.

    """

    def formatter(timestamp_timezone: str) -> str:
        """Convert a string containing a timestamp and maybe a timezone."""
        split = timestamp_timezone.split()
        date_time = datetime.fromtimestamp(int(split[0])).strftime(fmt)
        return f"{date_time} {split[1]}" if len(split) == 2 else date_time

    match = re.search("(?P<name>.*) (?P<email><.*>) (?P<date>.*)", data)
    if match:
        creator = match.group("name")
        email = match.group("email")
        date = formatter(match.group("date"))
        return creator, email, date

    raise ValueError("Creator pattern not matched.")

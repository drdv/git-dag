"""Test utils.py."""

# pylint: disable=missing-function-docstring

# docs.pytest.org/en/stable/example/parametrize.html#parametrizing-conditional-raising
from contextlib import nullcontext

import pytest

from git_dag import utils


@pytest.mark.parametrize(
    "message,expected",
    [
        (
            "Test without ASCII control characters €",
            "Test without ASCII control characters €",
        ),
        (
            "Test:                    € 日本語",  # pylint: disable=invalid-character-sub
            "Test: ^A ^B ^C ^D ^E ^F ^N ^O ^P ^Q ^R ^S ^T ^U ^V ^W ^X ^Y ^Z € 日本語",
        ),
        ("Test: , \b, \t, \n, , \f, \r €", "Test: , \b, \t, \n, , \f, \r €"),
    ],
)
def test_transform_ascii_control_chars(message: str, expected: str) -> None:
    assert utils.transform_ascii_control_chars(message) == expected


@pytest.mark.parametrize(
    "tagger_date,expected",
    [
        (
            "First Last <first.last@mail.com> 1739432921 +0100",
            nullcontext(
                (
                    "First Last",
                    "<first.last@mail.com>",
                    "Thu Feb 13 08:48:41 2025 +0100",
                )
            ),
        ),
        (
            "First Last <first.last@mail.com> 1739432921",
            nullcontext(
                (
                    "First Last",
                    "<first.last@mail.com>",
                    "Thu Feb 13 08:48:41 2025",
                )
            ),
        ),
        ("1739432921", pytest.raises(ValueError)),  # doesn't match
        ("First Last <first.last@mail.com> not-a-timestamp", pytest.raises(ValueError)),
    ],
)
def test_creator_timestamp_format(
    tagger_date: str,
    expected: nullcontext[tuple[str, str, str]],
) -> None:
    with expected as e:
        assert utils.creator_timestamp_format(tagger_date) == e


@pytest.mark.parametrize(
    "text,expected",
    [("a \\n b", "a \n b"), ("a \\\\n b", "a \\n b")],
)
def test_escape_decode(text: str, expected: str) -> None:
    assert utils.escape_decode(text) == expected

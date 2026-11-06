"""The find based _delimiter_positions must return exactly what the original character loop returned.

reference_positions below is the original implementation, copied without change. The
helper feeds fit(), preview_fit() and inspect_prefix(), so those are compared as well,
with the original helper put back in place.
"""

import random

import pytest

from autogrouper import AutoPrefixGrouper
from test_run_equivalence import FIT_DATASETS, FIT_SETTINGS, fit_outcome


def reference_positions(text, delimiter, skip_scheme_colon=True):
    positions = [i for i, ch in enumerate(text) if ch == delimiter]
    if skip_scheme_colon and delimiter == ":":
        positions = [i for i in positions if text[i + 1:i + 3] != "//"]
    return positions


HAND_MADE_TEXTS = [
    "",
    "a",
    ":",
    "/",
    "//",
    "///",
    "::",
    "http://example.org/gene/10",
    "https://example.org:8080/a/b",
    "DOID:0001816",
    "urn:isbn:0451450523",
    "http://a.org/x#y#z",
    ":://",
    "a:b://c",
    "x:/y",
    "x:/",
    "end:",
    ":start",
    "é/ü:β#",
    "\U0001F600:\U0001F600/",
    "no delimiter at all",
]
HAND_MADE_DELIMITERS = [":", "/", "#", "a", "\U0001F600", "é", "//", "::", "ab", ""]


@pytest.mark.parametrize("text", HAND_MADE_TEXTS)
@pytest.mark.parametrize("delimiter", HAND_MADE_DELIMITERS)
@pytest.mark.parametrize("skip_scheme_colon", [True, False])
def test_hand_made_texts_and_delimiters(text, delimiter, skip_scheme_colon):
    assert AutoPrefixGrouper._delimiter_positions(text, delimiter, skip_scheme_colon) == reference_positions(text, delimiter, skip_scheme_colon)


def test_random_texts_over_a_small_alphabet():
    generator = random.Random(20261106)
    alphabet = "ab:/#.//:x0é\U0001F600"
    for trial in range(40000):
        text = "".join(generator.choice(alphabet) for position in range(generator.randrange(0, 40)))
        for delimiter in (":", "/", "#", "a", "//", ""):
            for skip_scheme_colon in (True, False):
                assert AutoPrefixGrouper._delimiter_positions(text, delimiter, skip_scheme_colon) == reference_positions(text, delimiter, skip_scheme_colon)


def test_an_empty_delimiter_ends_and_gives_no_positions():
    assert AutoPrefixGrouper._delimiter_positions("abc", "") == []


def test_a_delimiter_of_two_characters_finds_nothing_as_before():
    assert AutoPrefixGrouper._delimiter_positions("a//b", "//") == []


@pytest.mark.parametrize("dataset_name", list(FIT_DATASETS))
@pytest.mark.parametrize("settings", FIT_SETTINGS, ids=lambda settings: str(settings))
def test_fit_gives_the_same_result_with_either_helper(dataset_name, settings, monkeypatch):
    strings = FIT_DATASETS[dataset_name]
    actual = fit_outcome(strings, settings)
    monkeypatch.setattr(AutoPrefixGrouper, "_delimiter_positions", staticmethod(reference_positions))
    expected = fit_outcome(strings, settings)
    assert actual == expected


@pytest.mark.parametrize("dataset_name", list(FIT_DATASETS))
@pytest.mark.parametrize("skip_scheme_colon", [True, False])
def test_preview_fit_gives_the_same_result_with_either_helper(dataset_name, skip_scheme_colon, monkeypatch):
    strings = FIT_DATASETS[dataset_name]

    def preview():
        try:
            return AutoPrefixGrouper().preview_fit(strings, prefix_depth=["#", ":", "/"], position_index=-1, skip_scheme_colon=skip_scheme_colon)
        except Exception as error:
            return ("error", type(error).__name__, str(error))

    actual = preview()
    monkeypatch.setattr(AutoPrefixGrouper, "_delimiter_positions", staticmethod(reference_positions))
    assert actual == preview()


@pytest.mark.parametrize("text", HAND_MADE_TEXTS)
@pytest.mark.parametrize("delimiter", [":", "/", "#"])
def test_inspect_prefix_prints_the_same_with_either_helper(text, delimiter, capsys, monkeypatch):
    AutoPrefixGrouper().inspect_prefix(text, delimiter)
    actual = capsys.readouterr().out
    monkeypatch.setattr(AutoPrefixGrouper, "_delimiter_positions", staticmethod(reference_positions))
    AutoPrefixGrouper().inspect_prefix(text, delimiter)
    assert actual == capsys.readouterr().out

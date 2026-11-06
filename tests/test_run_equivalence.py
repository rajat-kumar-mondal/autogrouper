"""The indexed _run must return exactly what the original quadratic _run returned.

reference_run below is the original implementation, copied without change. Every
test compares the two, including the order of the groups and the order of the
members inside each group.
"""

import itertools
import random
import time

import pytest

from autogrouper import AutoPrefixGrouper


def reference_run(strings):
    pending = list(strings)
    groups = {}

    while pending:
        current = pending[0]
        neighbour = pending[1] if len(pending) > 1 else current

        prefix = ""
        prefix_len = 0

        if len(current) == 0:
            groups.setdefault("", []).extend(x for x in pending if len(x) == 0)
            pending = [x for x in pending if len(x) > 0]
            continue

        compare_len = min(len(current), len(neighbour))
        for j in range(compare_len):
            if current[0] != neighbour[0]:
                prefix = current
                prefix_len = len(current)
                break
            if current[j] == neighbour[j]:
                prefix += current[j]
                prefix_len += 1
            else:
                break

        groups.setdefault(prefix, []).extend(
            x for x in pending if x[:prefix_len] == prefix
        )
        pending = [x for x in pending if x[:prefix_len] != prefix]

    return groups


def fit_sort(strings):
    return sorted(strings, key=lambda x: (x[0] if x else "", len(x)))


def assert_same(strings):
    expected = reference_run(strings)
    actual = AutoPrefixGrouper._run(strings)
    assert list(actual.items()) == list(expected.items())


def numbered_uris(count, prefix="http://scale.example/ns0/"):
    return [prefix + format(number, "07d") for number in range(count)]


HAND_MADE = [
    [],
    [""],
    ["", ""],
    ["a"],
    ["a", "a"],
    ["a", "a", "a"],
    ["a", "b"],
    ["ab", "abc", "abd", "b"],
    ["", "a", "ab", "b", ""],
    ["abc", "ab", "a"],
    ["a", "ab", "abc", "abcd", "abcde"],
    ["x", "xy", "xz", "y", "yz", "yzz"],
    ["same", "same", "same", "sama"],
    ["http://a/1", "http://a/2", "http://b/1", "ftp://a/1"],
    ["é", "éa", "éb", "ü", "üü"],
    ["\U0001F600", "\U0001F600a", "\U0001F601", "\U0010FFFF", "\U0010FFFFa"],
    ["a", "", "a", "", "ab"],
    ["ab", "a", "abc", "b", "ba", "a"],
]


@pytest.mark.parametrize("strings", HAND_MADE)
def test_hand_made_lists_in_the_order_given(strings):
    assert_same(strings)


@pytest.mark.parametrize("strings", HAND_MADE)
def test_hand_made_lists_in_the_order_fit_uses(strings):
    assert_same(fit_sort(strings))


@pytest.mark.parametrize("alphabet", ["ab", "abc", "ab/", "0123456789", "0a/:#"])
def test_random_lists_in_the_order_fit_uses(alphabet):
    generator = random.Random(alphabet)
    for trial in range(300):
        size = generator.randrange(0, 60)
        strings = ["".join(generator.choice(alphabet) for position in range(generator.randrange(0, 9))) for item in range(size)]
        assert_same(fit_sort(strings))


@pytest.mark.parametrize("alphabet", ["ab", "abc", "ab/", "0123456789", "0a/:#"])
def test_random_lists_in_any_order(alphabet):
    generator = random.Random("any order " + alphabet)
    for trial in range(300):
        size = generator.randrange(0, 60)
        strings = ["".join(generator.choice(alphabet) for position in range(generator.randrange(0, 9))) for item in range(size)]
        assert_same(strings)


def test_every_short_string_over_a_tiny_alphabet():
    strings = [""] + ["".join(chars) for length in range(1, 6) for chars in itertools.product("ab", repeat=length)]
    assert_same(fit_sort(strings))
    shuffled = list(strings)
    random.Random(7).shuffle(shuffled)
    assert_same(shuffled)


def test_heavy_duplication():
    generator = random.Random(11)
    strings = [generator.choice(["a", "ab", "abc", "b", "", "bb"]) for item in range(500)]
    assert_same(fit_sort(strings))
    assert_same(strings)


def test_numbered_uris_of_one_namespace():
    assert_same(fit_sort(numbered_uris(3000)))


def test_numbered_uris_of_several_namespaces_shuffled():
    strings = []
    for namespace in ("http://a.example/x/", "http://b.example/y#", "http://c.example/z:", "https://d.example/w/"):
        strings.extend(numbered_uris(400, namespace))
    random.Random(5).shuffle(strings)
    assert_same(fit_sort(strings))
    assert_same(strings)


def test_hash_like_identifiers():
    generator = random.Random(3)
    strings = ["http://h.example/id/" + format(generator.getrandbits(48), "012x") for item in range(2000)]
    assert_same(fit_sort(strings))


def test_prefixes_of_prefixes():
    strings = ["http://p.example/" + "a" * length for length in range(1, 80)] + ["http://p.example/" + "a" * 40 + "b" * length for length in range(1, 30)]
    assert_same(fit_sort(strings))
    assert_same(list(reversed(fit_sort(strings))))


def test_the_input_list_is_not_changed():
    strings = fit_sort(numbered_uris(50) + ["", "z"])
    copy = list(strings)
    AutoPrefixGrouper._run(strings)
    assert strings == copy


FIT_DATASETS = {
    "mixed uris": ["http://a.example/x/" + str(number) for number in range(60)] + ["http://b.example/y#T" + str(number) for number in range(40)]
                  + ["urn:isbn:" + str(number) for number in range(30)] + ["http://c.example/z:Q" + str(number) for number in range(30)],
    "numbered": numbered_uris(500),
    "plain words": ["apple", "apricot", "avocado", "banana", "blueberry", "cherry", "cranberry", "date", "fig", "grape", "grapefruit"],
    "with empties and repeats": ["", "a/b", "a/b", "a/c", "", "b/c/d", "b/c/e", "b"],
}

FIT_SETTINGS = [
    {},
    {"prefix_depth": "/"},
    {"prefix_depth": ["#", ":", "/"], "position_index": -1},
    {"prefix_depth": ["#", ":", "/"], "position_index": -1, "skip_scheme_colon": False},
    {"prefix_depth": ["/"], "position_index": 0},
    {"prefix_depth": ["/"], "position_index": 1},
    {"prefix_depth": ["#", "/"], "position_index": [-1, -1]},
    {"prefix_depth": ["/"], "position_index": -1, "resplit": True},
    {"prefix_depth": ["#", ":", "/"], "position_index": -1, "resplit": True},
]


def fit_outcome(strings, settings):
    try:
        grouper = AutoPrefixGrouper().fit(strings, **settings)
    except Exception as error:
        return ("error", type(error).__name__, str(error))
    return ("groups", list(grouper._groups.items()))


@pytest.mark.parametrize("dataset_name", list(FIT_DATASETS))
@pytest.mark.parametrize("settings", FIT_SETTINGS, ids=lambda settings: str(settings))
def test_fit_gives_the_same_result_with_either_run(dataset_name, settings, monkeypatch):
    strings = FIT_DATASETS[dataset_name]
    actual = fit_outcome(strings, settings)
    monkeypatch.setattr(AutoPrefixGrouper, "_run", staticmethod(reference_run))
    expected = fit_outcome(strings, settings)
    assert actual == expected


def best_of(repeats, strings):
    best = None
    for repeat in range(repeats):
        started = time.perf_counter()
        AutoPrefixGrouper().fit(strings, prefix_depth=["#", ":", "/"], position_index=-1)
        elapsed = time.perf_counter() - started
        best = elapsed if best is None else min(best, elapsed)
    return best


def test_numbered_uris_no_longer_grow_quadratically():
    small = best_of(3, numbered_uris(20000))
    large = best_of(3, numbered_uris(80000))
    assert large / small < 8


def falling_prefix_strings(length):
    """Equal length strings in pairs. Pair k shares exactly k leading letters, and the pairs come with k falling.

    Before the skip table, every round rescanned all the groups made earlier, which was the worst case of _run.
    """
    strings = []
    for k in range(length - 1, 0, -1):
        strings.append("a" * k + "b" + "c" * (length - k - 1))
        strings.append("a" * k + "c" + "c" * (length - k - 1))
    return strings


@pytest.mark.parametrize("length", [2, 3, 4, 5, 8, 20, 60])
def test_the_worst_case_family_matches_the_original(length):
    strings = falling_prefix_strings(length)
    assert_same(strings)
    assert_same(fit_sort(strings))
    assert_same(list(reversed(strings)))
    shuffled = list(strings)
    random.Random(length).shuffle(shuffled)
    assert_same(shuffled)


def test_the_worst_case_input_costs_about_as_much_as_the_same_strings_shuffled():
    ordered = falling_prefix_strings(3000)
    shuffled = list(ordered)
    random.Random(1).shuffle(shuffled)
    ordered_time = best_of(3, ordered)
    shuffled_time = best_of(3, shuffled)
    assert ordered_time / shuffled_time < 30

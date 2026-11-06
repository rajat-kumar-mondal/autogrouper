# Changelog

Author: Rajat Kumar Mondal

Each version lists what was fixed, what was added and what changed in behaviour. PyPI went from 0.2.2 to 0.2.5. Versions 0.2.3 and 0.2.4 exist on GitHub only, and 0.2.5 contains everything in them.

If you use 0.1.0 to 0.2.2, upgrade. Those versions can lose or repeat strings (see 0.2.3).

## 0.2.7 (6 November 2026)

A worst case guarantee. The groups are exactly the same.

Changed
* Each round searches an alphabetical copy of the strings for those that share its prefix. It used to step over strings that earlier rounds had already moved into a group. A table of the next live entry now skips them. The time is O(N log N x L) in every case.
* On strings of equal length that are arranged so that each round rescans every earlier group, `fit()` on 8000 strings of 4000 characters went from 1.44 seconds to 0.14 seconds. No ordinary input showed the problem, and ordinary inputs take about 1 to 4 percent longer.

Checked
* The worst case family joins the equivalence tests, together with a check that it costs about as much as the same strings in random order. That check fails on 0.2.6. Four deliberate bugs in the skip table were all caught, 180000 random lists gave identical results, and so did the 30 designed cases of schemamap.

## 0.2.6 (6 November 2026)

Faster again. The groups are exactly the same.

Changed
* The search for delimiters inside each string used a loop over every character in Python. It now uses the built in `find`, which runs in C. `fit()` on 800000 numbered URIs takes 1.1 seconds instead of 2.2, and on 800000 identifiers over five namespaces 1.5 seconds instead of 2.3. The algorithm is unchanged.

Checked
* 530 new test cases compare the new helper with a copy of the old one on hand made texts, random texts, and odd delimiters (empty, or longer than one character). They also compare `fit()`, `preview_fit()` and `inspect_prefix()` with the old helper put back. Three deliberate bugs in the helper were all caught. A further 40000 random lists with random settings gave identical results, and so did the 30 designed cases of schemamap.

## 0.2.5 (6 November 2026)

Faster grouping. The groups are exactly the same.

Fixed
* Grouping time grew with the square of the list when identifiers are numbered, such as `.../0000001`. `fit()` on 40000 numbered URIs took 4.9 seconds and now takes 0.11 seconds.

How
* Each round used to rebuild the whole list of pending strings. The pending strings now sit in a linked list, and an alphabetical copy finds the strings that share a prefix by binary search. The rounds, the groups and the order of the members are unchanged.

Checked
* 90 new tests compare the new code with a copy of the old code on hand made, random and structured lists, and on `fit()` with nine settings. A further 180000 random lists gave identical results.

Documentation
* The complexity in the README is corrected from O(N squared x L) to O(N log N x L), with a worst case of O(N x L squared).

## 0.2.4 (5 November 2026)

Fixed
* The colon of a URL scheme counted as a delimiter. With `prefix_depth=["#", ":", "/"]`, every URL without another colon was cut down to `http:`, because `:` is tried before `/` and every URL contains it.

Added
* `skip_scheme_colon` on `fit()`, `preview_fit()` and `inspect_prefix()`, default `True`. The colon that ends a URL scheme is no longer a delimiter, and `position_index` counting skips it. A URL such as `http://example.org/gene/10` falls through to `/`. An identifier such as `DOID:0001816` is still cut at its own colon.

Behaviour change
* A call that lists `":"` before `"/"` in `prefix_depth` now gives different groups than 0.2.3 for URLs that have no other colon. Pass `skip_scheme_colon=False` to get the old result.

## 0.2.3 (5 November 2026)

Fixed
* Strings could be lost or counted twice. When strings of different namespaces interleaved after sorting, the scan skipped some strings and collected others again, so group members and counts were wrong. Every input string now lands in exactly one group. Versions 0.1.0 to 0.2.2 are affected. URIs trigger it most often, because they all start with the same letter.

Behaviour change
* `fit()` and `preview_fit()` have a `resplit` parameter, default `False`. When `prefix_depth` is set, each string is cut once at the chosen delimiter and that cut is the final grouping. Identifiers such as UniProt accessions that start with different letters now stay under one prefix. Before 0.2.3 a group merged from several raw prefixes was split again when the characters right after the cut differed. Pass `resplit=True` to keep that old behaviour, for example to keep `GO_` and `RO_` apart when both are cut at `.../obo/`.

## 0.2.2 (4 November 2026)

Added
* `get_groups(strip_prefix=True)` removes the group key from the start of each member.
* `get_groups(count=True)` returns the number of members per group. The two options cannot be combined, and asking for both raises a `ValueError`.

Fixed
* The re-split step after a `prefix_depth` cut. A family such as `ggdonto#CON...` stays in one group, and strings from different namespaces such as `GO_` and `RO_` that are cut to the same prefix stay apart. Version 0.2.3 later made re-splitting optional.

## 0.2.1 (4 November 2026)

* Text only. Em dashes were removed from the docstrings and the README wording was tidied. The code did not change.

## 0.2.0 (4 November 2026)

Added
* `prefix_depth` accepts a list of delimiters and `position_index` accepts a list of integers. For each string the delimiters are tried in order, the first one found wins, and the string is cut once at the paired position. A single integer applies to every delimiter. Two lists must have the same length.

Documentation
* The README explains the list form.

## 0.1.1 (4 November 2026)

* The package description no longer contains an em dash.
* The algorithm diagram in the README uses an absolute URL, so it shows on the PyPI page.

## 0.1.0 (4 November 2026)

* First release. Groups strings by shared prefix without a delimiter, a prefix length or a schema.

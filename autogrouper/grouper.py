"""
Author: Rajat Kumar Mondal

Created: 2026-11-04
Last updated: 2026-11-04

autogrouper.grouper
~~~~~~~~~~~~~~~~~~~

AutoPrefixGrouper: automatic prefix-based grouping of string collections.

No external dependencies. Pure Python 3.6+.

Changes
-------
0.2.2
    ``get_groups()`` gains ``strip_prefix`` and ``count`` parameters.
    ``strip_prefix=True`` removes the group key from each member string.
    ``count=True`` returns ``dict[str, int]`` with member count per group.
    The two cannot be combined.

0.2.0
    ``prefix_depth`` and ``position_index`` now accept lists.
    When both are lists they must have the same length.
    For each string, delimiters are tried in order; the first one found
    wins and the string is cut once at the paired ``position_index``.
    A single ``position_index`` int applies to every delimiter in the list.

Problem
-------
Given an unsorted list of strings, automatically discover all shared
prefixes and group strings under them, with no prior knowledge of
prefix length, delimiter, or number of groups.

Algorithm
---------
1. Sort input by (first_char, length) so shortest strings anchor each
   namespace and strings from different namespaces never interleave.
2. Scan consecutive pairs to extract the longest common prefix.
3. Collect all strings matching that prefix in a single forward pass.
4. Repeat from the next unconsumed string.

Complexity
----------
Time : O(N^2 x L)  where N = number of strings, L = average length
Space: O(N x L)    to store the grouped output

"""

from __future__ import annotations


class AutoPrefixGrouper:
    """Automatic prefix-based grouper for string collections.

    Discovers shared prefixes from the data itself. No delimiter,
    no prefix length, and no prior schema knowledge required.

    Parameters
    ----------
    None

    Examples
    --------
    >>> g = AutoPrefixGrouper()
    >>> g.fit(["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"])
    AutoPrefixGrouper(fitted=True, n_strings=4, n_groups=2)
    >>> g.get_groups()
    {'rdf:': ['rdf:label', 'rdf:type'], 'owl:': ['owl:Class', 'owl:ObjectProperty']}
    >>> g.get_prefix_for("rdf:type")
    'rdf:'
    """

    def __init__(self) -> None:
        self._groups: dict[str, list[str]] = {}
        self._fitted: bool = False
        self._n_strings: int = 0

    # ------------------------------------------------------------------ #
    #  Core algorithm                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _run(strings: list[str]) -> dict[str, list[str]]:
        """Run the v5 prefix-grouping algorithm on a pre-sorted list.

        Parameters
        ----------
        strings : list[str]
            Input strings, sorted by (first_char, length).

        Returns
        -------
        dict[str, list[str]]
            Mapping of discovered prefix -> list of matching strings.
        """
        i = 0
        last_index = len(strings) - 1
        groups: dict[str, list[str]] = {}

        while i <= last_index:
            current = strings[i]
            try:
                neighbour = strings[i + 1]
            except IndexError:
                neighbour = strings[i]

            prefix = ""
            prefix_len = 0
            remaining = strings[i:]

            # Empty string branch: collect all consecutive empty strings
            if len(current) == 0:
                for x in remaining:
                    if len(x) == 0:
                        i += 1
                        groups.setdefault("", []).append("")

            # Non-empty string branch: find prefix from consecutive pair
            if len(current) > 0:
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
                for x in remaining:
                    if x[:prefix_len] == prefix:
                        i += 1
                        groups.setdefault(prefix, []).append(x)

        return groups

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def fit(self, strings: list,
            prefix_depth: "str | list[str] | None" = None,
            position_index: "int | list[int]" = -1) -> "AutoPrefixGrouper":
        """Discover prefix groups from a list of values.

        All values are accepted. Non-string values are converted to strings
        before processing, and a warning is printed listing the detected
        types. Only an empty list stops processing.

        Parameters
        ----------
        strings : list
            Any list of values. Need not be sorted. Duplicates are preserved.
            Empty strings are handled. Non-string elements (int, float, mixed)
            are converted to str with a printed warning.

        prefix_depth : str or list[str] or None, optional
            A delimiter character, or an ordered list of delimiter characters.
            When given, each discovered prefix is trimmed to end at a chosen
            occurrence of the matched delimiter.
            Default ``None`` means no trimming.

            When a list is given, delimiters are tried in the order supplied.
            For each string, the first delimiter found in that string wins.
            The string is cut exactly once, at the paired ``position_index``.
            If no delimiter in the list is found in a string, the original
            prefix from the algorithm is kept unchanged.

            Use :meth:`inspect_prefix` on a representative string to see
            which ``position_index`` suits your data.

        position_index : int or list[int], optional
            Which occurrence of the matched delimiter to trim at.
            Only used when ``prefix_depth`` is set.

            When ``position_index`` is a single ``int`` it applies to every
            delimiter in ``prefix_depth``.

            When ``position_index`` is a list it must have the same length as
            ``prefix_depth``. Each entry is paired positionally:
            ``prefix_depth[i]`` uses ``position_index[i]``.

            ``-1`` (default) trims at the last occurrence within the prefix.
            ``1`` trims at the first occurrence, ``2`` at the second, etc.

        Returns
        -------
        self : AutoPrefixGrouper
            Returns self to allow method chaining.

        Raises
        ------
        TypeError
            If ``strings`` is not a list.
        ValueError
            If ``strings`` is empty, ``prefix_depth`` contains an entry that
            is not a single character, or ``prefix_depth`` and
            ``position_index`` are both lists of different lengths.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
        >>> g.get_groups()
        {'rdf:': ['rdf:label', 'rdf:type']}

        >>> uris = [
        ...     "http://semanticscience.org/resource/SIO_000001",
        ...     "http://semanticscience.org/resource/SIO_000255",
        ... ]
        >>> g = AutoPrefixGrouper().fit(uris, prefix_depth="/", position_index=4)
        >>> g.get_groups()
        {'http://semanticscience.org/resource/': [...]}

        >>> # Mixed data: some strings use "#", others use "/"
        >>> mixed = [
        ...     "http://purl.obolibrary.org/obo/GO_0001234",
        ...     "http://purl.obolibrary.org/obo/GO_0005678",
        ...     "http://www.w3.org/2002/07/owl#Class",
        ...     "http://www.w3.org/2002/07/owl#ObjectProperty",
        ... ]
        >>> g = AutoPrefixGrouper().fit(
        ...     mixed,
        ...     prefix_depth=["#", "/"],
        ...     position_index=[-1, 5],
        ... )
        """
        if not isinstance(strings, list):
            raise TypeError(f"Expected list, got {type(strings).__name__}")
        if len(strings) == 0:
            raise ValueError(
                "Blank list detected. Cannot process an empty list."
            )

        # Normalise prefix_depth to list[str] or None
        if prefix_depth is not None:
            if isinstance(prefix_depth, str):
                prefix_depth = [prefix_depth]
            if not isinstance(prefix_depth, list):
                raise ValueError(
                    "prefix_depth must be a single character string or a list "
                    "of single character strings."
                )
            for d in prefix_depth:
                if not isinstance(d, str) or len(d) != 1:
                    raise ValueError(
                        f"Each entry in prefix_depth must be a single "
                        f"character string; got {d!r}."
                    )

        # Normalise position_index to list[int] or single int
        if prefix_depth is not None:
            if isinstance(position_index, list):
                if len(position_index) != len(prefix_depth):
                    raise ValueError(
                        f"prefix_depth has {len(prefix_depth)} entries but "
                        f"position_index has {len(position_index)}. "
                        f"They must have the same length, or supply a single "
                        f"int to apply to all delimiters."
                    )
            elif not isinstance(position_index, int):
                raise ValueError(
                    "position_index must be an int or a list of ints."
                )

        # Detect all unique types present in the input
        types_found = set(type(v).__name__ for v in strings)
        non_string_types = types_found - {"str"}

        if non_string_types:
            all_type_names = ", ".join(sorted(types_found))
            print(
                f"[autogrouper] Warning: multiple or non-string types detected: "
                f"{all_type_names}. "
                f"All values converted to string for processing."
            )
            strings = [str(v) for v in strings]

        sorted_strings = sorted(strings, key=lambda x: (x[0] if x else "", len(x)))
        raw_groups = self._run(sorted_strings)

        if prefix_depth is not None:
            self._groups = self._apply_prefix_depth(
                raw_groups, prefix_depth, position_index
            )
        else:
            self._groups = raw_groups

        self._fitted = True
        self._n_strings = len(strings)
        return self

    def get_groups(self,
                   strip_prefix: bool = False,
                   count: bool = False) -> "dict[str, list[str]] | dict[str, int]":
        """Return the discovered prefix groups.

        Parameters
        ----------
        strip_prefix : bool, optional
            When ``True``, each member string has the group key removed
            from its start, returning only the suffix portion.
            Default ``False`` returns full strings.
        count : bool, optional
            When ``True``, returns the number of members per group instead
            of the member list. Default ``False``.
            Cannot be combined with ``strip_prefix=True``.

        Returns
        -------
        dict[str, list[str]]
            Keys are discovered prefixes. Values are lists of strings
            that share that prefix (or their suffixes when
            ``strip_prefix=True``). Returned when ``count=False``.
        dict[str, int]
            Count of members per prefix. Returned when ``count=True``.

        Raises
        ------
        RuntimeError
            If called before :meth:`fit`.
        ValueError
            If both ``strip_prefix`` and ``count`` are ``True``.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(["os.path", "os.getcwd", "sys.argv"])
        >>> g.get_groups()
        {'os.': ['os.getcwd', 'os.path'], 'sys.argv': ['sys.argv']}
        >>> g.get_groups(strip_prefix=True)
        {'os.': ['getcwd', 'path'], 'sys.argv': ['']}
        >>> g.get_groups(count=True)
        {'os.': 2, 'sys.argv': 1}
        """
        self._check_fitted()
        if strip_prefix and count:
            raise ValueError(
                "strip_prefix and count cannot both be True. Choose one."
            )
        if count:
            return {prefix: len(members) for prefix, members in self._groups.items()}
        if strip_prefix:
            result: dict[str, list[str]] = {}
            for prefix, members in self._groups.items():
                plen = len(prefix)
                result[prefix] = [s[plen:] if s.startswith(prefix) else s for s in members]
            return result
        return dict(self._groups)

    def get_groups_recursive(self,
                              mode: str = "flat",
                              singletons: bool = True) -> dict:
        """Discover prefix groups at every level of depth recursively.

        Applies the same prefix-grouping algorithm repeatedly inside each
        group until no further sub-grouping is possible.

        Parameters
        ----------
        mode : str, optional
            Output structure. One of:

            ``"flat"`` (default)
                All prefix keys from every level are merged into a single
                flat dict. Coarser and finer prefixes coexist as separate
                keys. Easy to query by prefix at any depth.

            ``"nested"``
                Each group whose members can be further sub-grouped is
                replaced by a nested dict. Preserves the full hierarchy.

        singletons : bool, optional
            Whether to include sub-prefix keys that cover only one string.
            Default ``True`` (include all).

            ``True``
                Every discovered sub-prefix appears as a key, even if it
                covers only a single string. Use this when every string
                must be explicitly accounted for.

            ``False``
                Sub-prefix keys covering only one string are omitted.
                Use this for a cleaner view showing only meaningful
                groupings of two or more strings.

        Returns
        -------
        dict
            ``"flat"`` mode: ``dict[str, list[str]]``. Same shape as
            :meth:`get_groups` but with sub-prefix keys added at every
            depth level.

            ``"nested"`` mode: ``dict[str, list | dict]``. Values are
            either a list (leaf, no further sub-grouping possible) or a
            nested dict of the same shape.

        Raises
        ------
        RuntimeError
            If called before :meth:`fit`.
        ValueError
            If ``mode`` is not ``"flat"`` or ``"nested"``.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(
        ...     ["hasGlycan", "hasGlycanBinding", "hasX", "hasY", "abc"]
        ... )

        >>> g.get_groups_recursive(mode="flat", singletons=False)
        {'abc': ['abc'],
         'has': ['hasX', 'hasY', 'hasGlycan', 'hasGlycanBinding'],
         'hasGlycan': ['hasGlycan', 'hasGlycanBinding']}

        >>> g.get_groups_recursive(mode="flat", singletons=True)
        {'abc': ['abc'],
         'has': ['hasX', 'hasY', 'hasGlycan', 'hasGlycanBinding'],
         'hasGlycan': ['hasGlycan', 'hasGlycanBinding'],
         'hasX': ['hasX'],
         'hasY': ['hasY']}

        >>> g.get_groups_recursive(mode="nested", singletons=False)
        {'abc': ['abc'],
         'has': {'hasGlycan': ['hasGlycan', 'hasGlycanBinding']}}

        >>> g.get_groups_recursive(mode="nested", singletons=True)
        {'abc': ['abc'],
         'has': {'hasGlycan': ['hasGlycan', 'hasGlycanBinding'],
                 'hasX': ['hasX'],
                 'hasY': ['hasY']}}
        """
        self._check_fitted()
        if mode not in ("flat", "nested"):
            raise ValueError(f"mode must be 'flat' or 'nested', got '{mode}'")

        def _sub_group(known_prefix: str,
                       members: list[str]) -> dict[str, list[str]]:
            """Strip known_prefix, group suffixes, reattach prefix."""
            suffixes = [m[len(known_prefix):] for m in members]
            non_empty = [s for s in suffixes if s]
            if len(non_empty) <= 1:
                return {}
            sub = AutoPrefixGrouper()
            try:
                sub.fit(non_empty)
            except ValueError:
                return {}
            sub_groups = sub.get_groups()
            reattached: dict[str, list[str]] = {}
            for sub_prefix, sub_members in sub_groups.items():
                full_prefix = known_prefix + sub_prefix
                full_members = [known_prefix + m for m in sub_members]
                reattached[full_prefix] = full_members
            return reattached

        def _recurse_flat(known_prefix: str, members: list[str],
                          result: dict, seen: set) -> None:
            sub_groups = _sub_group(known_prefix, members)
            for sub_prefix, sub_members in sub_groups.items():
                if sub_prefix in seen:
                    continue
                is_singleton = len(sub_members) == 1
                if is_singleton and not singletons:
                    continue
                seen.add(sub_prefix)
                result[sub_prefix] = sub_members
                _recurse_flat(sub_prefix, sub_members, result, seen)

        def _recurse_nested(known_prefix: str,
                            members: list[str]) -> "dict | list":
            sub_groups = _sub_group(known_prefix, members)
            if not sub_groups:
                return members
            if len(sub_groups) == 1:
                only_key = next(iter(sub_groups))
                only_members = sub_groups[only_key]
                if set(only_members) == set(members):
                    return members
            nested: dict = {}
            for sub_prefix, sub_members in sub_groups.items():
                is_singleton = len(sub_members) == 1
                if is_singleton and not singletons:
                    continue
                nested[sub_prefix] = _recurse_nested(sub_prefix, sub_members)
            # Members not covered by any kept sub-group
            covered = {m for ms in nested.values()
                       for m in (ms if isinstance(ms, list)
                                 else _flatten(ms))}
            for m in members:
                if m not in covered:
                    if singletons:
                        nested[m] = [m]
            return nested if nested else members

        def _flatten(d: dict) -> list[str]:
            """Collect all string leaves from a nested dict."""
            out = []
            for v in d.values():
                if isinstance(v, list):
                    out.extend(v)
                else:
                    out.extend(_flatten(v))
            return out

        top_groups = self.get_groups()

        if mode == "flat":
            result: dict = {}
            seen: set = set(top_groups.keys())
            for prefix, members in top_groups.items():
                result[prefix] = members
                _recurse_flat(prefix, members, result, seen)
            return result

        nested_result: dict = {}
        for prefix, members in top_groups.items():
            nested_result[prefix] = _recurse_nested(prefix, members)
        return nested_result

    def get_prefix_for(self, string: str) -> str | None:
        """Return the discovered prefix that a given string belongs to.

        Parameters
        ----------
        string : str
            A string to look up.

        Returns
        -------
        str or None
            The prefix key the string is grouped under, or ``None`` if
            the string was not in the fitted data.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
        >>> g.get_prefix_for("rdf:type")
        'rdf:'
        >>> g.get_prefix_for("unknown") is None
        True
        """
        self._check_fitted()
        for prefix, members in self._groups.items():
            if string in members:
                return prefix
        return None

    def get_prefixes(self) -> list[str]:
        """Return the list of all discovered prefix keys.

        Returns
        -------
        list[str]
            Sorted list of discovered prefix strings.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(["rdf:type", "owl:Class", "rdfs:label"])
        >>> g.get_prefixes()
        ['owl:Class', 'rdf:', 'rdfs:']
        """
        self._check_fitted()
        return sorted(self._groups.keys())

    def get_strings_for(self, prefix: str) -> list[str]:
        """Return all strings grouped under a given prefix.

        Parameters
        ----------
        prefix : str
            A prefix key as returned by :meth:`get_prefixes`.

        Returns
        -------
        list[str]
            Strings grouped under that prefix, or empty list if not found.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
        >>> g.get_strings_for("rdf:")
        ['rdf:label', 'rdf:type']
        """
        self._check_fitted()
        return list(self._groups.get(prefix, []))

    def summary(self) -> dict[str, int]:
        """Return a count summary of strings per prefix group.

        Returns
        -------
        dict[str, int]
            Mapping of prefix -> number of strings in that group.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
        >>> g.summary()
        {'owl:Class': 1, 'rdf:': 2}
        """
        self._check_fitted()
        return {k: len(v) for k, v in sorted(self._groups.items())}

    def export(self, format: str = "json") -> str:
        """Serialise the fitted groups to a string in the requested format.

        Parameters
        ----------
        format : str
            One of ``"json"`` (default), ``"csv"``, ``"tsv"``, or
            ``"markdown"``.

            * **json**: a JSON object mapping each prefix to its list of
              strings.
            * **csv**: two columns, ``prefix`` and ``string``, one row per
              string. Header row always included. Fields containing commas or
              double-quotes are quoted per RFC 4180.
            * **tsv**: same layout as CSV but tab-separated. No quoting is
              applied; fields are written as-is.
            * **markdown**: a Markdown table with ``| prefix | string |``
              columns, suitable for README files and JOSS papers.

        Returns
        -------
        str
            The serialised groups.

        Raises
        ------
        RuntimeError
            If called before :meth:`fit`.
        ValueError
            If ``format`` is not one of the four supported values.

        Examples
        --------
        >>> g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
        >>> print(g.export("csv"))
        prefix,string
        owl:Class,owl:Class
        rdf:,rdf:label
        rdf:,rdf:type

        >>> print(g.export("markdown"))
        | prefix | string |
        | --- | --- |
        | owl:Class | owl:Class |
        | rdf: | rdf:label |
        | rdf: | rdf:type |
        """
        self._check_fitted()
        fmt = format.lower().strip()

        if fmt == "json":
            import json
            return json.dumps(
                {k: v for k, v in sorted(self._groups.items())},
                ensure_ascii=False,
                indent=2,
            )

        elif fmt == "csv":
            def _q(field: str) -> str:
                if any(ch in field for ch in (',', '"', '\n')):
                    return '"' + field.replace('"', '""') + '"'
                return field
            rows = ["prefix,string"]
            for prefix in sorted(self._groups):
                for string in sorted(self._groups[prefix]):
                    rows.append(f"{_q(prefix)},{_q(string)}")
            return "\n".join(rows)

        elif fmt == "tsv":
            rows = ["prefix\tstring"]
            for prefix in sorted(self._groups):
                for string in sorted(self._groups[prefix]):
                    rows.append(f"{prefix}\t{string}")
            return "\n".join(rows)

        elif fmt == "markdown":
            rows = ["| prefix | string |", "| --- | --- |"]
            for prefix in sorted(self._groups):
                for string in sorted(self._groups[prefix]):
                    rows.append(f"| {prefix} | {string} |")
            return "\n".join(rows)

        else:
            raise ValueError(
                f"Unsupported format {format!r}. "
                f"Choose 'json', 'csv', 'tsv', or 'markdown'."
            )

    def inspect_prefix(self, string: str, delimiter: str) -> None:
        """Print every position_index value for a delimiter in a string.

        Use this before calling :meth:`fit` with ``prefix_depth`` to see
        exactly which ``position_index`` produces the prefix boundary you
        want.

        Does not require :meth:`fit` to have been called first.

        Parameters
        ----------
        string : str
            A representative string from your data.
        delimiter : str
            A single character to inspect positions of.

        Raises
        ------
        ValueError
            If ``delimiter`` is not a single character.

        Examples
        --------
        >>> g = AutoPrefixGrouper()
        >>> g.inspect_prefix(
        ...     "http://semanticscience.org/resource/SIO_000001",
        ...     delimiter="/"
        ... )
        position_index=1 : "http:/"
        position_index=2 : "http://"
        position_index=3 : "http://semanticscience.org/"
        position_index=4 : "http://semanticscience.org/resource/"
        position_index=5 : "http://semanticscience.org/resource/SIO_000001"
        """
        if not isinstance(delimiter, str) or len(delimiter) != 1:
            raise ValueError("delimiter must be a single character string.")
        positions = [i for i, ch in enumerate(string) if ch == delimiter]
        if not positions:
            print(f'[autogrouper] "{delimiter}" not found in the string.')
            return
        for idx, pos in enumerate(positions, start=1):
            trimmed = string[:pos + 1]
            print(f'position_index={idx} : "{trimmed}"')

    def preview_fit(self, strings: list,
                    prefix_depth: "str | list[str]",
                    position_index: "int | list[int]" = -1) -> dict:
        """Return what :meth:`fit` would produce without changing object state.

        Use this to verify grouping output before committing to :meth:`fit`.
        The object's fitted state is not changed.

        Parameters
        ----------
        strings : list
            The same list you plan to pass to :meth:`fit`.
        prefix_depth : str or list[str]
            Single delimiter or ordered list of delimiters. Same as
            :meth:`fit`.
        position_index : int or list[int], optional
            Which occurrence to trim at. Same as :meth:`fit`.
            Default ``-1`` (last occurrence within the prefix).

        Returns
        -------
        dict[str, list[str]]
            Preview of the groups that :meth:`fit` would produce.

        Examples
        --------
        >>> uris = [
        ...     "http://semanticscience.org/resource/SIO_000001",
        ...     "http://semanticscience.org/resource/SIO_000255",
        ... ]
        >>> g = AutoPrefixGrouper()
        >>> g.preview_fit(uris, prefix_depth="/", position_index=4)
        {'http://semanticscience.org/resource/': [...]}
        """
        temp = AutoPrefixGrouper()
        temp.fit(strings, prefix_depth=prefix_depth,
                 position_index=position_index)
        return temp.get_groups()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _check_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError(
                "AutoPrefixGrouper is not fitted yet. Call fit() first."
            )

    @staticmethod
    def _resolve_cut(string: str,
                     delimiters: "list[str]",
                     indices: "list[int]") -> "tuple[str, int] | None":
        """Return (delimiter, position_index) for the first delimiter found in string.

        Tries delimiters in order. Returns ``None`` if none are found.

        Parameters
        ----------
        string : str
            The string to inspect.
        delimiters : list[str]
            Ordered list of single-character delimiters.
        indices : list[int]
            Paired position indices, same length as ``delimiters``.

        Returns
        -------
        tuple[str, int] or None
            The winning (delimiter, position_index) pair, or None.
        """
        for delimiter, idx in zip(delimiters, indices):
            if delimiter in string:
                return (delimiter, idx)
        return None

    @staticmethod
    def _trim_prefix(prefix: str, delimiter: str, position_index: int) -> str:
        """Trim ``prefix`` to end at the chosen occurrence of ``delimiter``.

        Parameters
        ----------
        prefix : str
            The prefix string to trim.
        delimiter : str
            Single character to trim at.
        position_index : int
            -1 for last occurrence, 1 for first, 2 for second, etc.

        Returns
        -------
        str
            Trimmed prefix, or the original prefix if ``delimiter`` is not
            found or ``position_index`` is out of range.
        """
        positions = [i for i, ch in enumerate(prefix) if ch == delimiter]
        if not positions:
            return prefix
        if position_index == -1:
            cut = positions[-1]
        elif 1 <= position_index <= len(positions):
            cut = positions[position_index - 1]
        else:
            return prefix
        return prefix[:cut + 1]

    @staticmethod
    def _apply_prefix_depth(groups: dict,
                             delimiters: "list[str]",
                             position_index: "int | list[int]") -> dict:
        """Trim each prefix key using the first matching delimiter per string.

        For each string in a group, the delimiter list is tried in order.
        The first delimiter found in that string determines where the prefix
        is cut. Each string is cut at most once.

        After trimming, groups that collapse to the same key are re-split
        by running the algorithm again on their combined members, so that
        distinct sub-groups are not lost.

        Parameters
        ----------
        groups : dict[str, list[str]]
            Raw groups from ``_run``.
        delimiters : list[str]
            Ordered list of single-character delimiters.
        position_index : int or list[int]
            When a single int, it applies to all delimiters.
            When a list, each entry is paired positionally with ``delimiters``.

        Returns
        -------
        dict[str, list[str]]
            Groups with trimmed prefix keys. Groups that merged after
            trimming are re-split where possible.
        """
        # Build a paired indices list of the same length as delimiters
        if isinstance(position_index, int):
            indices = [position_index] * len(delimiters)
        else:
            indices = list(position_index)

        # Step 1: re-bucket each string under its trimmed prefix.
        # Track which original raw prefixes contributed to each new bucket.
        merged: dict[str, list[str]] = {}
        origin_raw_prefixes: dict[str, set] = {}  # new_prefix -> set of raw prefixes

        for prefix, members in groups.items():
            # Determine a new prefix for each member string individually
            # (members in the same raw group may contain different delimiters)
            per_string: dict[str, str] = {}  # original string -> new prefix
            for s in members:
                cut_info = AutoPrefixGrouper._resolve_cut(s, delimiters, indices)
                if cut_info is None:
                    # No delimiter matched in this string; keep the raw prefix
                    per_string[s] = prefix
                else:
                    delim, idx = cut_info
                    per_string[s] = AutoPrefixGrouper._trim_prefix(s, delim, idx)

            # Group strings by their new prefix
            new_prefix_to_strings: dict[str, list[str]] = {}
            for s, np in per_string.items():
                new_prefix_to_strings.setdefault(np, []).append(s)

            for np, strs in new_prefix_to_strings.items():
                merged.setdefault(np, []).extend(strs)
                origin_raw_prefixes.setdefault(np, set()).add(prefix)

        # Step 2: for buckets that absorbed strings from multiple different raw
        # prefixes, attempt a re-split only when those strings have genuinely
        # different leading characters after the trimmed prefix. This keeps
        # GO_ and RO_ separate (different first chars) while keeping all
        # ggdonto#CON* strings together (same first char after the # cut).
        result: dict[str, list[str]] = {}
        for new_prefix, members in merged.items():
            n_origins = len(origin_raw_prefixes[new_prefix])
            if n_origins > 1 and len(members) > 1:
                # Check whether members diverge in the first character that
                # follows the trimmed prefix.
                plen = len(new_prefix)
                first_chars = {s[plen] if len(s) > plen else "" for s in members}
                if len(first_chars) > 1:
                    # Genuinely different namespaces merged. Re-split.
                    sorted_members = sorted(
                        members, key=lambda x: (x[0] if x else "", len(x))
                    )
                    sub_groups = AutoPrefixGrouper._run(sorted_members)
                    if len(sub_groups) > 1:
                        for sub_prefix, sub_members in sub_groups.items():
                            result.setdefault(sub_prefix, []).extend(sub_members)
                    else:
                        result.setdefault(new_prefix, []).extend(members)
                else:
                    # Same leading character after prefix. Same namespace.
                    # Keep as one group.
                    result.setdefault(new_prefix, []).extend(members)
            else:
                result.setdefault(new_prefix, []).extend(members)
        return result

    # ------------------------------------------------------------------ #
    #  Dunder methods                                                      #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        if self._fitted:
            return (
                f"AutoPrefixGrouper("
                f"fitted=True, "
                f"n_strings={self._n_strings}, "
                f"n_groups={len(self._groups)})"
            )
        return "AutoPrefixGrouper(fitted=False)"

    def __len__(self) -> int:
        """Return number of discovered groups."""
        self._check_fitted()
        return len(self._groups)

    def __contains__(self, prefix: str) -> bool:
        """Check if a prefix key exists in the groups."""
        self._check_fitted()
        return prefix in self._groups

    def __iter__(self):
        """Iterate over (prefix, strings) pairs."""
        self._check_fitted()
        return iter(self._groups.items())

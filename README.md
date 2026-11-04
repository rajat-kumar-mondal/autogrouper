# autogrouper

Automatic prefix-based grouping of string collections. No delimiter. No schema. No external dependencies. Pure Python 3.6+.

[![PyPI version](https://badge.fury.io/py/autogrouper.svg)](https://pypi.org/project/autogrouper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

---

## The story 📖

While working with large collections of ontology terms and semantic web URIs, a simple need came up: group these strings by their shared prefix. The strings looked like `rdf:type`, `owl:Class`, `GO:0001234`, `http://purl.obolibrary.org/obo/RO_0000001`. Hundreds of them, from different namespaces, mixed together in a flat list.

The obvious question was: does a tool exist that can do this automatically, without being told what the delimiter is, without a predefined schema, without any prior knowledge of the data?

After searching through Python libraries, bioinformatics tools, and string processing utilities, the answer was no. Everything found either required you to specify a delimiter, a regex pattern, or a known prefix list upfront. Nothing could look at a flat list of strings and simply discover the structure on its own.

So `autogrouper` was built to do exactly that.

---

## What it does ✨

Given a flat list of strings, `autogrouper` automatically finds the shared prefix between strings and groups them under it. You do not need to know the prefix, its length, its delimiter, or how many groups exist. The algorithm discovers all of that from the data.

```python
from autogrouper import AutoPrefixGrouper

strings = [
    "user_id", "user_name", "user_email",
    "order_id", "order_date", "order_total",
    "product_id", "product_name",
]

AutoPrefixGrouper().fit(strings).get_groups()

# {
#     "order_":   ["order_date", "order_id", "order_total"],
#     "product_": ["product_id", "product_name"],
#     "user_":    ["user_email", "user_id", "user_name"],
# }
```

---

## Installation

```bash
pip install autogrouper
```

Requires Python 3.6 or later. No external dependencies.

---

## Basic usage

```python
from autogrouper import AutoPrefixGrouper

g = AutoPrefixGrouper()
g.fit(["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"])
g.get_groups()
# {"owl:": ["owl:Class", "owl:ObjectProperty"], "rdf:": ["rdf:label", "rdf:type"]}
```

`fit()` stores the result inside the object. All other methods read from that stored result. Call `fit()` once before anything else.

### Method chaining

`fit()` returns `self`, so you can chain:

```python
groups = AutoPrefixGrouper().fit(strings).get_groups()
```

---

## Understanding the output

The key in each group is the **longest common character-level prefix** shared by the strings in that group. It is not based on any delimiter.

```python
AutoPrefixGrouper().fit(["GO:0001234", "GO:0005678"]).get_groups()
# {"GO:000": ["GO:0001234", "GO:0005678"]}
```

The algorithm found `GO:000` because that is the longest prefix shared by both strings, not `GO:`. Use `prefix_depth` and `position_index` if you want to control where the prefix stops.

A string with no matching partner receives its own key:

```python
AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"]).get_groups()
# {"owl:Class": ["owl:Class"], "rdf:": ["rdf:label", "rdf:type"]}
```

`owl:Class` has no neighbour that starts with `owl:`, so it becomes its own key.

---

## Controlling prefix depth

Sometimes the algorithm finds a prefix that is longer than you want. For example:

```python
uris = [
    "http://semanticscience.org/resource/SIO_000001",
    "http://semanticscience.org/resource/SIO_000255",
    "http://semanticscience.org/resource/SIO_000772",
]

AutoPrefixGrouper().fit(uris).get_groups()
# {"http://semanticscience.org/resource/SIO_000": [...]}
```

You may want the prefix to stop at `http://semanticscience.org/resource/` instead. Use `prefix_depth` and `position_index` on `fit()`.

### Step 1: inspect the string

Use `inspect_prefix()` on a representative string to see what each `position_index` value produces:

```python
g = AutoPrefixGrouper()
g.inspect_prefix("http://semanticscience.org/resource/SIO_000001", "/")

# position_index=1 : "http:/"
# position_index=2 : "http://"
# position_index=3 : "http://semanticscience.org/"
# position_index=4 : "http://semanticscience.org/resource/"
# position_index=5 : "http://semanticscience.org/resource/SIO_000001"
```

`inspect_prefix()` does not require `fit()` to have been called first.

### Step 2: preview the result

Use `preview_fit()` to see what `fit()` would produce before committing:

```python
g.preview_fit(uris, prefix_depth="/", position_index=4)
# {"http://semanticscience.org/resource/": [...]}
```

`preview_fit()` does not change the fitted state of the object.

### Step 3: fit with the chosen depth

```python
g.fit(uris, prefix_depth="/", position_index=4)
g.get_groups()
# {"http://semanticscience.org/resource/": [
#     "http://semanticscience.org/resource/SIO_000001",
#     "http://semanticscience.org/resource/SIO_000255",
#     "http://semanticscience.org/resource/SIO_000772",
# ]}
```

`position_index=-1` (the default) trims at the last occurrence of the delimiter within the discovered prefix.

### When groups collapse after trimming

If two separate groups trim to the same prefix, `autogrouper` automatically re-runs the algorithm on the combined members to restore the distinction:

```python
strings = [
    "http://purl.obolibrary.org/obo/GO_0000001",
    "http://purl.obolibrary.org/obo/GO_0000002",
    "http://purl.obolibrary.org/obo/RO_0000001",
    "http://purl.obolibrary.org/obo/RO_0000002",
]

AutoPrefixGrouper().fit(strings, prefix_depth="/", position_index=4).get_groups()
# {
#     "http://purl.obolibrary.org/obo/GO_000000": ["...GO_0000001", "...GO_0000002"],
#     "http://purl.obolibrary.org/obo/RO_000000": ["...RO_0000001", "...RO_0000002"],
# }
```

Both groups were originally trimmed to `http://purl.obolibrary.org/obo/` but the algorithm detected that they could be split further and did so automatically.

---

## Recursive grouping

`get_groups_recursive()` applies the algorithm inside each group repeatedly until no further sub-grouping is possible.

```python
strings = ["hasGlycan", "hasGlycanBinding", "hasX", "hasY", "abc"]
g = AutoPrefixGrouper().fit(strings)
```

The top-level result groups everything starting with `has` together:

```python
g.get_groups()
# {"abc": ["abc"], "has": ["hasGlycan", "hasGlycanBinding", "hasX", "hasY"]}
```

`get_groups_recursive()` goes deeper and finds `hasGlycan` inside the `has` group:

```python
g.get_groups_recursive(mode="flat", singletons=False)
# {
#     "abc":       ["abc"],
#     "has":       ["hasGlycan", "hasGlycanBinding", "hasX", "hasY"],
#     "hasGlycan": ["hasGlycan", "hasGlycanBinding"],
# }
```

### mode parameter

`mode="flat"` (default) merges all levels into one dict. Coarser and finer prefixes appear as separate keys side by side.

`mode="nested"` keeps the hierarchy. Each group that could be sub-grouped becomes a nested dict:

```python
g.get_groups_recursive(mode="nested", singletons=False)
# {
#     "abc": ["abc"],
#     "has": {"hasGlycan": ["hasGlycan", "hasGlycanBinding"]},
# }
```

### singletons parameter

`singletons=True` (default) includes sub-prefix keys that cover only one string:

```python
g.get_groups_recursive(mode="flat", singletons=True)
# {
#     "abc":       ["abc"],
#     "has":       ["hasGlycan", "hasGlycanBinding", "hasX", "hasY"],
#     "hasGlycan": ["hasGlycan", "hasGlycanBinding"],
#     "hasX":      ["hasX"],
#     "hasY":      ["hasY"],
# }
```

`singletons=False` omits them, showing only groups with two or more members.

---

## Lookup methods

```python
g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"])

g.get_prefix_for("rdf:type")       # "rdf:"
g.get_prefix_for("unknown")        # None
g.get_prefixes()                   # ["owl:", "rdf:"]
g.get_strings_for("owl:")          # ["owl:Class", "owl:ObjectProperty"]
g.summary()                        # {"owl:": 2, "rdf:": 2}
```

---

## Python operators

```python
len(g)        # number of discovered groups
"rdf:" in g   # True if that prefix key exists
```

Iteration yields `(prefix, members)` pairs:

```python
for prefix, members in g:
    print(prefix, members)
```

`repr()` shows the fitted state:

```python
repr(g)
# "AutoPrefixGrouper(fitted=True, n_strings=4, n_groups=2)"
```

---

## Export

Serialise the fitted groups to a string for downstream use.

```python
g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"])
```

**JSON** (default):

```python
print(g.export("json"))
# {
#   "owl:": ["owl:Class", "owl:ObjectProperty"],
#   "rdf:": ["rdf:label", "rdf:type"]
# }
```

**CSV**:

```python
print(g.export("csv"))
# prefix,string
# owl:,owl:Class
# owl:,owl:ObjectProperty
# rdf:,rdf:label
# rdf:,rdf:type
```

**TSV**:

```python
print(g.export("tsv"))
# prefix	string
# owl:	owl:Class
# ...
```

**Markdown**:

```python
print(g.export("markdown"))
# | prefix | string |
# | --- | --- |
# | owl: | owl:Class |
# ...
```

Format names are case-insensitive. `export()` with no argument defaults to JSON.

To write to a file:

```python
with open("groups.json", "w") as f:
    f.write(g.export("json"))
```

---

## Non-string inputs

If the list contains integers, floats, or a mix of types, `autogrouper` converts everything to string and prints a warning:

```python
AutoPrefixGrouper().fit([1, 2, 10, 11, 100])
# [autogrouper] Warning: multiple or non-string types detected: int.
# All values converted to string for processing.
```

An empty list raises `ValueError`. Duplicate strings are preserved.

---

## Where can you use this? 🗺️

`autogrouper` is useful whenever you have a flat list of strings that carry hidden structure in their prefixes and you want to surface that structure without writing custom parsing code.

**Semantic web and ontologies**
You are working with RDF triples, OWL classes, or ontology term IDs from databases like GO, CHEBI, or SIO. The terms arrive as a flat list from a SPARQL query. `autogrouper` groups them by namespace instantly, with no hardcoded prefix list.

**Bioinformatics identifiers**
Accession numbers, gene IDs, protein IDs, and pathway identifiers from multiple databases land in the same column. `autogrouper` separates them by their natural prefix pattern (`ENSG`, `hsa-mir`, `UniRef50_`, `IPR`) without you knowing those patterns in advance.

**Log analysis**
Cloud service logs, S3 keys, or application log lines share structural prefixes like `prod/api/`, `prod/db/`, `staging/api/`. `autogrouper` groups them so you can analyse each subsystem separately.

**API and schema exploration**
You receive a JSON response or a database schema you have never seen before. Field names like `user_id`, `user_name`, `order_id`, `order_total` carry their own grouping. `autogrouper` surfaces it in one line.

**File system analysis**
A list of file paths from an unfamiliar directory tree. `autogrouper` groups them by shared path prefix so you can see the structure before you decide what to do with the files.

**Configuration and environment variables**
Environment variables like `DB_HOST`, `DB_PORT`, `DB_NAME`, `REDIS_HOST`, `REDIS_PORT` are easier to audit and validate when grouped by their natural prefix.

**Any flat list you did not design**
If you received the list from a third-party API, a collaborator, or a legacy system and want to understand its structure quickly, `autogrouper` is the first tool to reach for.

---

## Full API reference

| Method | Requires fit | Description |
|---|---|---|
| `fit(strings, prefix_depth, position_index)` | No | Discover groups. Returns `self`. |
| `get_groups()` | Yes | `dict[str, list[str]]` of all groups. |
| `get_groups_recursive(mode, singletons)` | Yes | Groups at every depth level. |
| `get_prefix_for(string)` | Yes | Prefix key for a string, or `None`. |
| `get_prefixes()` | Yes | Sorted list of all prefix keys. |
| `get_strings_for(prefix)` | Yes | All strings under a prefix. |
| `summary()` | Yes | `dict[str, int]` count per prefix. |
| `export(format)` | Yes | Serialise to `json`, `csv`, `tsv`, or `markdown`. |
| `inspect_prefix(string, delimiter)` | No | Print `position_index=N` values for a delimiter. |
| `preview_fit(strings, prefix_depth, position_index)` | No | Dry run without changing state. |
| `len(g)` | Yes | Number of groups. |
| `prefix in g` | Yes | Check if a prefix key exists. |
| `for prefix, members in g` | Yes | Iterate over groups. |

---

## Algorithm

Input strings are sorted by `(first_char, length)`. This keeps strings from the same namespace together and places the shortest string at the front of each block.

The algorithm scans consecutive pairs. For each pair, it extracts the longest common character-level prefix. All remaining strings that begin with that prefix are collected in one forward pass. The scan then advances to the next unconsumed string and repeats.

Time complexity: O(N squared x L), where N is the number of strings and L is average string length.
Space complexity: O(N x L).

No trie, hash table, or suffix array is required. Zero imports. Runs on CPython 3.6+.

---

## AI usage disclosure 🤖

This package was built by Rajat Kumar Mondal. The core algorithm, its design, and all architectural decisions are original.

Claude Sonnet 4.6 by Anthropic was used during development. Specifically, it assisted with code review and edge case identification, writing and refining docstrings, generating and expanding the test suite from an initial set to 287 cases, and structuring and writing this documentation.

The model was accessed through the Claude.ai interface. No other AI tools, code generation assistants, or large language models were used at any stage.

All output from the model was reviewed manually before inclusion. Every test case was checked against real algorithm output. Any suggested code that did not match observed behaviour was corrected or discarded.

---

## Development

```bash
git clone https://github.com/rajat-kumar-mondal/autogrouper
cd autogrouper
pip install -e ".[dev]"
pytest
```

287 test cases cover the core algorithm, recursive grouping, prefix depth control, inspect, preview, and all four export formats.

---

## Citation

If you use this package in academic work, please cite:

```bibtex
@article{autogrouper2026,
  title   = {autogrouper: Automatic Prefix-Based Grouping of String Collections},
  journal = {Journal of Open Source Software},
  year    = {2026},
  note    = {Submitted}
}
```

---

## Contributing

Contributions are welcome. If you find a bug, have a feature request, or want to improve the documentation, open an issue or a pull request on GitHub. Please include a minimal reproducible example when reporting a bug.

---

## License

MIT 2026

---

Built with love 💙 & overthinking.

Inspired by intuition and simplicity.

Drinking Boss Black Coffee and Itoen Oi Tea while building.

Beautified and documented with Claude.

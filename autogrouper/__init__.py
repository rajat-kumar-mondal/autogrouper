"""
autogrouper
~~~~~~~~~~~

Automatic prefix-based grouping of string collections.
Zero dependencies. Pure Python 3.6+.

Author: Rajat Kumar Mondal

Created: 2026-11-04
Last updated: 2026-11-04

Basic usage::

    from autogrouper import AutoPrefixGrouper

    g = AutoPrefixGrouper()
    g.fit(["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"])
    print(g.get_groups())
    # {'owl:': ['owl:Class', 'owl:ObjectProperty'], 'rdf:': ['rdf:label', 'rdf:type']}

"""

from .grouper import AutoPrefixGrouper

__version__ = "0.1.1"
__license__ = "MIT"

__all__ = ["AutoPrefixGrouper"]

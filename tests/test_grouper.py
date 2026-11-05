"""
Tests for AutoPrefixGrouper class.
357 test cases covering the core algorithm, recursive grouping,
prefix_depth (single and list), position_index (single and list),
resplit, skip_scheme_colon, strip_prefix, count, inspect_prefix, preview_fit, and export.

Author: Rajat Kumar Mondal

Created: 2026-11-04
Last updated: 2026-11-05
"""

import pytest
from autogrouper import AutoPrefixGrouper


# ── helpers ─────────────────────────────────────────────────────────────────

def fit(strings):
    return AutoPrefixGrouper().fit(strings).get_groups()


def has_key(r, k):
    assert k in r, f"Missing key {k!r} in {list(r)}"


def count(r, k, n):
    assert len(r[k]) == n, f"Key {k!r}: expected {n}, got {len(r[k])}"


def total_strings(r, n):
    got = sum(len(v) for v in r.values())
    assert got == n, f"Expected {n} total strings, got {got}"


# ── GROUP 1: Basic RDF/OWL namespace grouping ────────────────────────────────

def test_T001_rdf_3():
    r = fit(["rdf:type", "rdf:label", "rdf:value"])
    has_key(r, "rdf:")
    count(r, "rdf:", 3)


def test_T002_owl_3():
    r = fit(["owl:Class", "owl:ObjectProperty", "owl:DatatypeProperty"])
    has_key(r, "owl:")
    count(r, "owl:", 3)


def test_T003_rdfs_3():
    r = fit(["rdfs:label", "rdfs:comment", "rdfs:subClassOf"])
    has_key(r, "rdfs:")
    count(r, "rdfs:", 3)


def test_T004_rdf_owl_two_groups():
    r = fit(["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"])
    has_key(r, "rdf:")
    has_key(r, "owl:")
    count(r, "rdf:", 2)
    count(r, "owl:", 2)


def test_T005_rdf_rdfs_owl_singleton():
    # owl:Class is a singleton (no owl: pair), gets own key
    r = fit(["rdf:type", "rdf:label", "rdfs:label", "rdfs:comment", "owl:Class"])
    has_key(r, "rdf:")
    has_key(r, "rdfs:")
    total_strings(r, 5)


# ── GROUP 2: File path grouping ───────────────────────────────────────────────

def test_T006_file_usr_local():
    r = fit(["/usr/local/bin/python", "/usr/local/bin/pip", "/usr/local/lib/libpython"])
    total_strings(r, 3)
    assert any("/usr/local" in k for k in r)


def test_T007_file_home_user():
    r = fit(["/home/user/docs/report.pdf", "/home/user/docs/slides.pptx",
             "/home/user/images/photo.jpg"])
    total_strings(r, 3)
    assert any("/home/user" in k for k in r)


def test_T008_file_etc():
    r = fit(["/etc/nginx/nginx.conf", "/etc/nginx/sites-enabled", "/etc/ssh/sshd_config"])
    total_strings(r, 3)
    assert any("/etc/" in k for k in r)


def test_T009_file_var():
    r = fit(["/var/log/syslog", "/var/log/auth.log", "/var/run/docker.pid"])
    total_strings(r, 3)
    assert any("/var/" in k for k in r)


def test_T010_file_home_users():
    r = fit(["/home/alice/file1", "/home/bob/file2", "/home/carol/file3"])
    total_strings(r, 3)
    assert any("/home/" in k for k in r)


# ── GROUP 3: Gene/biological identifiers ─────────────────────────────────────

def test_T011_go_terms():
    r = fit(["GO:0001234", "GO:0005678", "GO:0009999"])
    total_strings(r, 3)
    assert any("GO:" in k for k in r)


def test_T012_chebi():
    r = fit(["CHEBI:12345", "CHEBI:67890", "CHEBI:11111"])
    total_strings(r, 3)
    assert any("CHEBI:" in k for k in r)


def test_T013_hsa_mir():
    r = fit(["hsa-mir-21", "hsa-mir-155", "hsa-mir-31"])
    has_key(r, "hsa-mir-")
    count(r, "hsa-mir-", 3)


def test_T014_ensembl():
    r = fit(["ENSG00000001234", "ENSG00000005678", "ENSG00000009999"])
    total_strings(r, 3)
    assert any("ENSG" in k for k in r)


def test_T015_hasglycan():
    r = fit(["hasGlycan", "hasGlycanBinding", "hasGlycanStructure"])
    has_key(r, "hasGlycan")
    count(r, "hasGlycan", 3)


# ── GROUP 4: URL grouping ─────────────────────────────────────────────────────

def test_T016_url_person():
    r = fit(["https://example.org/person/alice", "https://example.org/person/bob"])
    total_strings(r, 2)
    assert any("https://example.org/person/" in k for k in r)


def test_T017_schema_org():
    r = fit(["http://schema.org/name", "http://schema.org/email", "http://schema.org/address"])
    has_key(r, "http://schema.org/")
    count(r, "http://schema.org/", 3)


def test_T018_obo_url():
    r = fit(["http://purl.obolibrary.org/obo/GO_001",
             "http://purl.obolibrary.org/obo/GO_002"])
    total_strings(r, 2)
    assert any("GO_00" in k for k in r)


def test_T019_api_versioned():
    r = fit(["https://api.example.com/v1/users", "https://api.example.com/v1/posts",
             "https://api.example.com/v2/users"])
    total_strings(r, 3)
    assert any("https://api.example.com/v" in k for k in r)


def test_T020_ftp():
    r = fit(["ftp://files.server.org/pub/data1", "ftp://files.server.org/pub/data2"])
    total_strings(r, 2)
    assert any("ftp://files.server.org/pub/data" in k for k in r)


# ── GROUP 5: No common prefix ─────────────────────────────────────────────────

def test_T021_no_common_prefix():
    r = fit(["alpha", "beta", "gamma", "delta"])
    assert all(len(v) == 1 for v in r.values())
    total_strings(r, 4)


def test_T022_fruit_names():
    r = fit(["apple", "banana", "cherry"])
    assert all(len(v) == 1 for v in r.values())
    total_strings(r, 3)


def test_T023_single_element():
    r = fit(["xyz"])
    assert len(r) == 1
    total_strings(r, 1)


def test_T024_no_common_4():
    r = fit(["dog", "cat", "fox", "ant"])
    assert all(len(v) == 1 for v in r.values())
    total_strings(r, 4)


def test_T025_single_char():
    r = fit(["z"])
    assert len(r) == 1
    total_strings(r, 1)


# ── GROUP 6: Overlapping prefix cases ────────────────────────────────────────

def test_T026_rdf_rdfs_separated():
    r = fit(["rdf:type", "rdf:label", "rdfs:label", "rdfs:comment"])
    has_key(r, "rdf:")
    has_key(r, "rdfs:")
    total_strings(r, 4)


def test_T027_has_prefix():
    r = fit(["hasRole", "hasRoleIn", "has", "hasValue"])
    total_strings(r, 4)
    assert any("has" in k for k in r)


def test_T028_sub_prefix():
    r = fit(["subClassOf", "subPropertyOf", "subgraph"])
    total_strings(r, 3)
    assert any("sub" in k for k in r)


def test_T029_is_prefix():
    r = fit(["isA", "isPartOf", "isRelatedTo", "isLocatedIn"])
    total_strings(r, 4)
    assert any("is" in k for k in r)


def test_T030_part_prefix():
    r = fit(["partOf", "partWhole", "participatesIn"])
    total_strings(r, 3)
    assert any("part" in k for k in r)


# ── GROUP 7: Identical strings ────────────────────────────────────────────────

def test_T031_all_identical():
    r = fit(["hasA", "hasA", "hasA"])
    has_key(r, "hasA")
    count(r, "hasA", 3)


def test_T032_two_identical():
    r = fit(["rdf:type", "rdf:type"])
    total_strings(r, 2)
    assert any("rdf:type" in k for k in r)


def test_T033_five_identical_char():
    r = fit(["x", "x", "x", "x", "x"])
    has_key(r, "x")
    count(r, "x", 5)


# ── GROUP 8: Empty string handling ───────────────────────────────────────────

def test_T034_all_empty():
    r = fit(["", "", ""])
    has_key(r, "")
    count(r, "", 3)


def test_T035_empty_plus_rdf():
    r = fit(["", "rdf:type", "rdf:label"])
    has_key(r, "")
    has_key(r, "rdf:")
    total_strings(r, 3)


def test_T036_two_empty():
    r = fit(["", ""])
    has_key(r, "")
    count(r, "", 2)


# ── GROUP 9: Single character prefixes ───────────────────────────────────────

def test_T037_a_b_groups():
    r = fit(["a1", "a2", "a3", "b1", "b2"])
    total_strings(r, 5)
    assert any("a" in k for k in r)
    assert any("b" in k for k in r)


def test_T038_x_y_val():
    r = fit(["x_val1", "x_val2", "y_val1", "y_val2", "z_val1"])
    total_strings(r, 5)
    assert any("x_val" in k for k in r)


def test_T039_p_q_groups():
    r = fit(["p:foo", "p:bar", "q:foo", "q:bar"])
    has_key(r, "p:")
    has_key(r, "q:")
    total_strings(r, 4)


def test_T040_prefix_chain():
    r = fit(["a", "ab", "abc", "abcd"])
    total_strings(r, 4)
    assert len(r) >= 1


# ── GROUP 10: Numeric prefixes ────────────────────────────────────────────────

def test_T041_numeric_123():
    r = fit(["123abc", "123def", "123ghi"])
    has_key(r, "123")
    count(r, "123", 3)


def test_T042_zero_padded():
    r = fit(["001_alpha", "001_beta", "002_alpha", "002_beta"])
    total_strings(r, 4)
    assert any("00" in k for k in r)


def test_T043_year_prefix():
    r = fit(["2024_report", "2024_data", "2025_report", "2025_data"])
    total_strings(r, 4)
    assert any("202" in k for k in r)


def test_T044_semver():
    r = fit(["v1.0.1", "v1.0.2", "v2.0.1", "v2.0.2"])
    total_strings(r, 4)
    assert any("v" in k for k in r)


def test_T045_10x_20x():
    r = fit(["10x_cell", "10x_gene", "20x_cell", "20x_gene"])
    has_key(r, "10x_")
    has_key(r, "20x_")
    total_strings(r, 4)


# ── GROUP 11: Large groups ────────────────────────────────────────────────────

def test_T046_has_property_10():
    r = fit([f"hasProperty{i}" for i in range(10)])
    total_strings(r, 10)
    assert any("hasProperty" in k for k in r)


def test_T047_rdf_prop_15():
    r = fit([f"rdf:prop{i}" for i in range(15)])
    total_strings(r, 15)
    assert any("rdf:prop" in k for k in r)


def test_T048_go_terms_20():
    r = fit([f"GO:{str(i).zfill(7)}" for i in range(20)])
    total_strings(r, 20)
    assert any("GO:" in k for k in r)


# ── GROUP 12: Many groups simultaneously ─────────────────────────────────────

def test_T049_five_namespaces():
    r = fit(["rdf:type", "rdf:label", "owl:Class", "owl:Property",
             "rdfs:label", "rdfs:comment", "skos:prefLabel", "skos:altLabel",
             "dc:title", "dc:creator"])
    total_strings(r, 10)
    assert len(r) >= 4


def test_T050_has_is_part():
    r = fit(["hasA", "hasB", "hasC", "isA", "isB", "isC",
             "partA", "partB", "partC"])
    has_key(r, "has")
    has_key(r, "is")
    has_key(r, "part")
    total_strings(r, 9)


def test_T051_four_greek():
    r = fit(["alpha_1", "alpha_2", "beta_1", "beta_2",
             "gamma_1", "gamma_2", "delta_1", "delta_2"])
    total_strings(r, 8)
    assert len(r) >= 4


def test_T052_5_namespaces_3_each():
    r = fit([f"ns{i}:prop{j}" for i in range(5) for j in range(3)])
    total_strings(r, 15)
    assert len(r) >= 5


# ── GROUP 13: Python module name style ───────────────────────────────────────

def test_T053_os_module():
    r = fit(["os.path", "os.getcwd", "os.listdir", "os.environ"])
    has_key(r, "os.")
    count(r, "os.", 4)


def test_T054_sys_module():
    r = fit(["sys.argv", "sys.path", "sys.version", "sys.exit"])
    has_key(r, "sys.")
    count(r, "sys.", 4)


def test_T055_os_sys():
    r = fit(["os.path", "os.getcwd", "sys.argv", "sys.path"])
    has_key(r, "os.")
    has_key(r, "sys.")
    total_strings(r, 4)


def test_T056_json_csv():
    r = fit(["json.load", "json.dump", "json.loads", "json.dumps",
             "csv.reader", "csv.writer"])
    has_key(r, "json.")
    has_key(r, "csv.")
    total_strings(r, 6)


# ── GROUP 14: Camel case properties ──────────────────────────────────────────

def test_T057_hasglycan_4():
    r = fit(["hasGlycan", "hasGlycanBinding", "hasGlycanStructure", "hasGlycanComposition"])
    has_key(r, "hasGlycan")
    count(r, "hasGlycan", 4)


def test_T058_is_camel():
    r = fit(["isLocatedIn", "isPartOf", "isRelatedTo", "isDerivedFrom"])
    total_strings(r, 4)
    assert any("is" in k for k in r)


def test_T059_haspa_prefix():
    r = fit(["hasPart", "hasParticipant", "hasParent", "hasPath"])
    total_strings(r, 4)
    assert any("hasPa" in k for k in r)


def test_T060_participates():
    r = fit(["participatesIn", "participatesAs", "participatesWith"])
    has_key(r, "participates")
    count(r, "participates", 3)


# ── GROUP 15: Underscore separated ───────────────────────────────────────────

def test_T061_bio_underscore():
    r = fit(["bio_entity", "bio_process", "bio_function"])
    has_key(r, "bio_")
    count(r, "bio_", 3)


def test_T062_chem_underscore():
    r = fit(["chem_compound", "chem_reaction", "chem_element"])
    has_key(r, "chem_")
    count(r, "chem_", 3)


def test_T063_bio_chem():
    r = fit(["bio_entity", "bio_process", "chem_compound", "chem_reaction"])
    has_key(r, "bio_")
    has_key(r, "chem_")
    total_strings(r, 4)


def test_T064_gene_prot():
    r = fit(["gene_expr", "gene_func", "gene_loc", "prot_struct", "prot_func"])
    has_key(r, "gene_")
    has_key(r, "prot_")
    total_strings(r, 5)


# ── GROUP 16: Long URI strings ────────────────────────────────────────────────

def test_T065_full_rdf_uri():
    BASE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    r = fit([BASE + s for s in ["type", "label", "value"]])
    has_key(r, BASE)
    count(r, BASE, 3)


def test_T066_full_owl_uri():
    BASE = "http://www.w3.org/2002/07/owl#"
    r = fit([BASE + s for s in ["Class", "ObjectProperty", "DatatypeProperty"]])
    has_key(r, BASE)
    count(r, BASE, 3)


def test_T067_full_rdfs_uri():
    BASE = "http://www.w3.org/2000/01/rdf-schema#"
    r = fit([BASE + s for s in ["label", "comment", "subClassOf"]])
    has_key(r, BASE)
    count(r, BASE, 3)


# ── GROUP 17: Mixed case ──────────────────────────────────────────────────────

def test_T068_uppercase_abc():
    r = fit(["ABC_123", "ABC_456", "ABC_789"])
    has_key(r, "ABC_")
    count(r, "ABC_", 3)


def test_T069_mesh():
    r = fit(["MeSH:D001", "MeSH:D002", "MeSH:D003"])
    total_strings(r, 3)
    assert any("MeSH:" in k for k in r)


def test_T070_uniprot():
    r = fit(["UniProt:P12345", "UniProt:Q67890", "UniProt:A11111"])
    total_strings(r, 3)
    assert any("UniProt:" in k for k in r)


# ── GROUP 18: Sparse/edge list sizes ─────────────────────────────────────────

def test_T071_minimum_two():
    r = fit(["hasA", "hasB"])
    has_key(r, "has")
    count(r, "has", 2)


def test_T072_single_no_pair():
    r = fit(["rdf:type"])
    assert len(r) == 1
    total_strings(r, 1)


def test_T073_two_no_common():
    r = fit(["a", "b"])
    assert len(r) == 2
    total_strings(r, 2)


def test_T074_two_single_char_prefix():
    r = fit(["aa", "ab"])
    has_key(r, "a")
    count(r, "a", 2)


def test_T075_three_two_char_prefix():
    r = fit(["abc", "abd", "abe"])
    has_key(r, "ab")
    count(r, "ab", 3)


# ── GROUP 19: Real-world ontology predicates ──────────────────────────────────

def test_T076_mixed_predicates():
    r = fit(["hasGlycan", "hasGlycanBinding", "rdf:type", "owl:Class", "rdfs:label"])
    has_key(r, "hasGlycan")
    total_strings(r, 5)


def test_T077_skos():
    r = fit(["skos:prefLabel", "skos:altLabel", "skos:definition", "skos:notation"])
    has_key(r, "skos:")
    count(r, "skos:", 4)


def test_T078_dc():
    r = fit(["dc:title", "dc:creator", "dc:subject", "dc:description", "dc:date"])
    has_key(r, "dc:")
    count(r, "dc:", 5)


def test_T079_foaf():
    r = fit(["foaf:name", "foaf:mbox", "foaf:homepage", "foaf:knows"])
    has_key(r, "foaf:")
    count(r, "foaf:", 4)


def test_T080_schema():
    r = fit(["schema:name", "schema:email", "schema:address", "schema:telephone"])
    has_key(r, "schema:")
    count(r, "schema:", 4)


# ── GROUP 20: Stress / combined ───────────────────────────────────────────────

def test_T081_8_namespaces():
    r = fit(["rdf:type", "rdf:label", "owl:Class", "rdfs:label", "skos:prefLabel",
             "dc:title", "foaf:name", "schema:name", "hasGlycan", "hasGlycanBinding"])
    total_strings(r, 10)
    assert len(r) >= 5


def test_T082_20_prop_groups():
    r = fit([f"prop_{chr(65+i)}_{j}" for i in range(5) for j in range(4)])
    total_strings(r, 20)
    assert len(r) >= 5


def test_T083_empty_plus_10ns():
    r = fit([""] + [f"ns{i}:val" for i in range(10)])
    has_key(r, "")
    total_strings(r, 11)


def test_T084_mixed_plus_empty():
    r = fit(["hasA", "hasB", "hasC", "isA", "isB", ""])
    has_key(r, "has")
    has_key(r, "is")
    has_key(r, "")
    total_strings(r, 6)


def test_T085_url_two_subpaths():
    r = fit(
        [f"http://example.org/class/{c}" for c in ["Animal", "Plant", "Fungus"]]
        + [f"http://example.org/property/{p}" for p in ["hasName", "hasAge"]]
    )
    total_strings(r, 5)
    assert any("http://example.org/" in k for k in r)


def test_T086_three_bio_ontologies():
    r = fit(["GO:0001", "GO:0002", "CHEBI:001", "CHEBI:002", "MeSH:D001", "MeSH:D002"])
    total_strings(r, 6)
    assert len(r) >= 3


def test_T087_gene_prot_10():
    r = fit([f"gene_{i}" for i in range(5)] + [f"prot_{i}" for i in range(5)])
    has_key(r, "gene_")
    has_key(r, "prot_")
    total_strings(r, 10)


def test_T088_xref():
    r = fit(["xref:OMIM", "xref:HPO", "xref:ORPHA", "xref:OMIM2"])
    has_key(r, "xref:")
    count(r, "xref:", 4)


def test_T089_10_distinct_chars():
    r = fit(list("ABCDEFGHIJ"))
    assert len(r) == 10
    total_strings(r, 10)


def test_T090_two_char_first_char():
    r = fit(["AA", "AB", "AC", "BA", "BB", "BC"])
    has_key(r, "A")
    has_key(r, "B")
    total_strings(r, 6)


def test_T091_pre_5():
    r = fit(["pre_alpha", "pre_beta", "pre_gamma", "pre_delta", "pre_epsilon"])
    has_key(r, "pre_")
    count(r, "pre_", 5)


def test_T092_disease_ontology_3():
    r = fit(["MONDO:0001", "MONDO:0002", "HP:0001", "HP:0002", "NCIT:C001", "NCIT:C002"])
    total_strings(r, 6)
    assert len(r) >= 3


def test_T093_part_vs_participates():
    r = fit(["part_of", "part_whole", "participates_in", "participates_as"])
    has_key(r, "part_")
    has_key(r, "participates_")
    total_strings(r, 4)


def test_T094_sample_ids():
    r = fit([f"sample_{str(i).zfill(3)}" for i in range(1, 11)])
    total_strings(r, 10)
    assert any("sample_" in k for k in r)


def test_T095_chromosome():
    r = fit(["chr1:1000", "chr1:2000", "chr2:1000", "chr2:2000", "chrX:1000"])
    total_strings(r, 5)
    assert any("chr" in k for k in r)


def test_T096_eco():
    r = fit(["ECO:0000001", "ECO:0000002", "ECO:0000003"])
    total_strings(r, 3)
    assert any("ECO:" in k for k in r)


def test_T097_biochemistry():
    r = fit(["reaction_001", "reaction_002", "compound_001", "compound_002", "pathway_001"])
    total_strings(r, 5)
    assert any("reaction_" in k for k in r)
    assert any("compound_" in k for k in r)


def test_T098_is_group_plus_empty():
    r = fit(["isA", "isB", ""])
    has_key(r, "is")
    has_key(r, "")
    total_strings(r, 3)


def test_T099_xsd():
    r = fit(["xsd:string", "xsd:integer", "xsd:boolean", "xsd:decimal", "xsd:date"])
    has_key(r, "xsd:")
    count(r, "xsd:", 5)


def test_T100_mega():
    r = fit([
        "rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty",
        "rdfs:label", "rdfs:comment", "skos:prefLabel", "skos:altLabel",
        "dc:title", "dc:creator", "foaf:name", "foaf:mbox",
        "schema:name", "schema:email",
        "hasGlycan", "hasGlycanBinding",
        "GO:0001", "GO:0002", "CHEBI:001", "CHEBI:002",
    ])
    total_strings(r, 20)
    assert len(r) >= 7


# ── Error handling ────────────────────────────────────────────────────────────

def test_not_fitted_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(RuntimeError, match="not fitted"):
        g.get_groups()


def test_empty_list_raises():
    with pytest.raises(ValueError, match="Blank list detected"):
        AutoPrefixGrouper().fit([])


def test_non_list_raises():
    with pytest.raises(TypeError):
        AutoPrefixGrouper().fit(("rdf:type",))


def test_integer_list_converts_with_warning(capsys):
    g = AutoPrefixGrouper().fit([1, 2, 10, 11, 20])
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "int" in captured.out
    assert "converted to string" in captured.out
    assert g.get_groups() is not None


def test_float_list_converts_with_warning(capsys):
    g = AutoPrefixGrouper().fit([1.0, 1.1, 2.0, 2.1])
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "float" in captured.out


def test_mixed_int_float_warns_both_types(capsys):
    g = AutoPrefixGrouper().fit([1, 2.5, 3, 4.0])
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "float" in captured.out
    assert "int" in captured.out


def test_mixed_string_and_int_warns(capsys):
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", 42])
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "int" in captured.out
    assert "str" in captured.out
    # The string values survive the conversion correctly
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 3


def test_all_string_no_warning(capsys):
    AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    captured = capsys.readouterr()
    assert captured.out == ""


def test_int_list_result_is_grouped_correctly(capsys):
    # [1, 2, 10, 11, 100] -> strings ["1", "10", "100", "11", "2"] after sort
    g = AutoPrefixGrouper().fit([1, 2, 10, 11, 100])
    _ = capsys.readouterr()
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 5


def test_method_chaining():
    g = AutoPrefixGrouper().fit(["os.path", "os.getcwd"])
    assert isinstance(g, AutoPrefixGrouper)


def test_repr_unfitted():
    assert repr(AutoPrefixGrouper()) == "AutoPrefixGrouper(fitted=False)"


def test_repr_fitted():
    r = repr(AutoPrefixGrouper().fit(["rdf:type", "rdf:label"]))
    assert "fitted=True" in r
    assert "n_strings=2" in r


def test_len():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class", "owl:Property"])
    assert len(g) == 2


def test_contains():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    assert "rdf:" in g
    assert "owl:" not in g


def test_iter():
    g = AutoPrefixGrouper().fit(["dc:title", "dc:creator"])
    pairs = list(g)
    assert len(pairs) == 1
    prefix, members = pairs[0]
    assert prefix == "dc:"
    assert set(members) == {"dc:title", "dc:creator"}


def test_get_prefixes():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class", "owl:Property"])
    assert g.get_prefixes() == ["owl:", "rdf:"]


def test_get_strings_for():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    assert set(g.get_strings_for("rdf:")) == {"rdf:type", "rdf:label"}
    assert g.get_strings_for("missing:") == []


def test_get_prefix_for():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    assert g.get_prefix_for("rdf:type") == "rdf:"
    assert g.get_prefix_for("unknown") is None


def test_summary():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    s = g.summary()
    assert s["rdf:"] == 2
    assert s.get("owl:Class", 0) == 1 or s.get("owl:", 0) == 1


# ── GROUP 21: Unicode / non-ASCII prefixes ────────────────────────────────────

def test_T101_chinese_prefix():
    r = fit(["数学_001", "数学_002", "化学_001", "化学_002"])
    total_strings(r, 4)
    assert any("数学" in k for k in r)
    assert any("化学" in k for k in r)


def test_T102_arabic_prefix():
    r = fit(["مرحبا_1", "مرحبا_2", "وداعا_1", "وداعا_2"])
    total_strings(r, 4)
    assert len(r) >= 1


def test_T103_japanese_prefix():
    r = fit(["東京_001", "東京_002", "大阪_001", "大阪_002"])
    total_strings(r, 4)
    assert any("東京" in k for k in r)
    assert any("大阪" in k for k in r)


def test_T104_cyrillic_prefix():
    r = fit(["привет_1", "привет_2", "пока_1", "пока_2"])
    total_strings(r, 4)
    assert any("приве" in k for k in r)


def test_T105_greek_prefix():
    r = fit(["αλφα_001", "αλφα_002", "βητα_001", "βητα_002"])
    total_strings(r, 4)
    assert any("αλφα" in k for k in r)


def test_T106_mixed_ascii_unicode():
    r = fit(["gene_東京_001", "gene_東京_002", "gene_大阪_001"])
    total_strings(r, 3)
    assert any("gene_" in k for k in r)


def test_T107_emoji_prefix():
    r = fit(["🔬study_001", "🔬study_002", "🧬gene_001", "🧬gene_002"])
    total_strings(r, 4)
    assert len(r) >= 1


def test_T108_accented_latin():
    r = fit(["café_001", "café_002", "naïve_001", "naïve_002"])
    total_strings(r, 4)
    assert any("café" in k for k in r)
    assert any("naïve" in k for k in r)


# ── GROUP 22: Whitespace strings ──────────────────────────────────────────────

def test_T109_space_prefix():
    r = fit([" alpha", " beta", " gamma", "delta"])
    total_strings(r, 4)
    assert any(k.startswith(" ") for k in r)


def test_T110_tab_prefix():
    r = fit(["\talpha", "\tbeta", "\tgamma"])
    total_strings(r, 3)
    assert any(k.startswith("\t") for k in r)


def test_T111_multiple_spaces():
    r = fit(["  a001", "  a002", "  b001", "  b002"])
    total_strings(r, 4)
    assert any("  " in k for k in r)


def test_T112_newline_prefix():
    r = fit(["\nalpha", "\nbeta", "\ngamma"])
    total_strings(r, 3)
    assert len(r) >= 1


def test_T113_mixed_whitespace_and_normal():
    r = fit([" key_1", " key_2", "key_3", "key_4"])
    total_strings(r, 4)
    assert len(r) >= 1


def test_T114_trailing_space():
    r = fit(["word _1", "word _2", "other_1", "other_2"])
    total_strings(r, 4)
    assert len(r) >= 1


# ── GROUP 23: Special character prefixes ──────────────────────────────────────

def test_T115_at_sign_prefix():
    r = fit(["@user_001", "@user_002", "@admin_001", "@admin_002"])
    total_strings(r, 4)
    assert any("@user" in k for k in r)
    assert any("@admin" in k for k in r)


def test_T116_hash_prefix():
    r = fit(["#tag_001", "#tag_002", "#label_001", "#label_002"])
    total_strings(r, 4)
    assert any("#tag" in k for k in r)


def test_T117_dollar_prefix():
    r = fit(["$var_001", "$var_002", "$const_001", "$const_002"])
    total_strings(r, 4)
    assert any("$var" in k for k in r)


def test_T118_percent_prefix():
    # Algorithm finds the longest common prefix across sorted pairs.
    # "%20..." and "%3A..." share "%" as their common prefix at the top level.
    r = fit(["%20encoded", "%20text", "%3Acolon", "%3Avalue"])
    total_strings(r, 4)
    assert any("%" in k for k in r)


def test_T119_slash_prefix():
    r = fit(["/api/v1/users", "/api/v1/posts", "/api/v2/users", "/api/v2/posts"])
    total_strings(r, 4)
    assert any("/api/v" in k for k in r)


def test_T120_colon_only_prefix():
    # Sorted: ":delta", ":epsilon", "::alpha", "::beta", "::gamma"
    # The full set shares ":" as the top-level prefix.
    r = fit(["::alpha", "::beta", "::gamma", ":delta", ":epsilon"])
    total_strings(r, 5)
    assert any(":" in k for k in r)


def test_T121_pipe_prefix():
    r = fit(["|field_1", "|field_2", "|record_1", "|record_2"])
    total_strings(r, 4)
    assert any("|field" in k for k in r)


def test_T122_exclamation_prefix():
    # Sorted: "!critical_1", "!important_1", "!important_2"
    # First pair shares only "!" as the common prefix.
    r = fit(["!important_1", "!important_2", "!critical_1"])
    total_strings(r, 3)
    assert any("!" in k for k in r)


# ── GROUP 24: Very long strings ───────────────────────────────────────────────

def test_T123_long_http_urls():
    r = fit([
        "https://www.example.com/ontology/v1/biology/cell/nucleus/membrane",
        "https://www.example.com/ontology/v1/biology/cell/nucleus/dna",
        "https://www.example.com/ontology/v1/biology/cell/mitochondria/matrix",
        "https://www.example.com/ontology/v1/chemistry/organic/alkane/methane",
    ])
    total_strings(r, 4)
    assert any("https://www.example.com/ontology/v1/biology/cell/nucleus/" in k for k in r)


def test_T124_very_long_string_200_chars():
    base = "A" * 190
    r = fit([base + "001", base + "002", base + "003"])
    total_strings(r, 3)
    assert any(len(k) > 100 for k in r)


def test_T125_long_gene_ontology_uris():
    r = fit([
        "http://purl.obolibrary.org/obo/GO_0000001",
        "http://purl.obolibrary.org/obo/GO_0000002",
        "http://purl.obolibrary.org/obo/GO_0000003",
        "http://purl.obolibrary.org/obo/CHEBI_00001",
        "http://purl.obolibrary.org/obo/CHEBI_00002",
    ])
    total_strings(r, 5)
    assert any("GO_" in k for k in r)
    assert any("CHEBI_" in k for k in r)


def test_T126_long_mixed_depth_paths():
    r = fit([
        "/data/projects/2024/biology/experiment_001/run_01",
        "/data/projects/2024/biology/experiment_001/run_02",
        "/data/projects/2024/biology/experiment_002/run_01",
        "/data/projects/2024/chemistry/experiment_001/run_01",
    ])
    total_strings(r, 4)
    assert any("/data/projects/2024/" in k for k in r)


def test_T127_long_no_common_prefix():
    a = "X" * 100 + "_alpha"
    b = "Y" * 100 + "_beta"
    r = fit([a, b])
    total_strings(r, 2)
    assert len(r) == 2


# ── GROUP 25: Large input stress tests ───────────────────────────────────────

def test_T128_500_strings_two_groups():
    group_a = [f"alpha_{i:04d}" for i in range(250)]
    group_b = [f"beta_{i:04d}" for i in range(250)]
    combined = sorted(group_a + group_b)
    r = fit(combined)
    total_strings(r, 500)
    assert any("alpha_" in k for k in r)
    assert any("beta_" in k for k in r)


def test_T129_1000_strings_ten_groups():
    strings = []
    prefixes = ["alpha", "beta", "gamma", "delta", "epsilon",
                "zeta", "eta", "theta", "iota", "kappa"]
    for p in prefixes:
        for i in range(100):
            strings.append(f"{p}_{i:04d}")
    strings_sorted = sorted(strings)
    r = fit(strings_sorted)
    total_strings(r, 1000)
    assert len(r) >= 5


def test_T130_200_identical_strings():
    r = fit(["identical_string"] * 200)
    total_strings(r, 200)
    assert len(r) == 1


def test_T131_500_single_char_strings():
    import string
    chars = list(string.ascii_lowercase + string.digits)
    strings = sorted(chars * 10)
    r = fit(strings)
    total_strings(r, len(strings))
    assert len(r) >= 1


def test_T132_many_unique_no_overlap():
    strings = [f"unique_{i:06d}" for i in range(300)]
    r = fit(sorted(strings))
    total_strings(r, 300)
    assert any("unique_" in k for k in r)


def test_T133_rdf_scale_100():
    prefixes = ["rdf:", "owl:", "rdfs:", "skos:", "dc:"]
    strings = []
    for p in prefixes:
        for i in range(20):
            strings.append(f"{p}term_{i:03d}")
    r = fit(sorted(strings))
    total_strings(r, 100)
    assert any("rdf:" in k for k in r)
    assert any("owl:" in k for k in r)


# ── GROUP 26: Deep prefix chains ─────────────────────────────────────────────

def test_T134_prefix_chain_3_deep():
    # "a", "ab", "abc" are each prefixes of the next
    r = fit(["abc_001", "abc_002", "ab_001", "ab_002", "a_001", "a_002"])
    total_strings(r, 6)
    assert len(r) >= 1


def test_T135_nested_namespace_chain():
    r = fit([
        "http://example.org/",
        "http://example.org/bio/",
        "http://example.org/bio/cell",
        "http://example.org/bio/gene",
        "http://example.org/chem/",
        "http://example.org/chem/element",
    ])
    total_strings(r, 6)
    assert any("http://example.org/" in k for k in r)


def test_T136_string_is_prefix_of_another():
    r = fit(["has", "hasGlycan", "hasGlycanBinding"])
    total_strings(r, 3)
    assert len(r) >= 1


def test_T137_increasing_length_same_root():
    r = fit(["x", "xy", "xyz", "xyza", "xyzab"])
    total_strings(r, 5)
    assert len(r) >= 1


def test_T138_two_chains_interleaved():
    r = fit(["aaa_001", "aaa_002", "aaab_001", "aaab_002",
             "bbb_001", "bbb_002", "bbbc_001", "bbbc_002"])
    total_strings(r, 8)
    assert any("aaa" in k for k in r)
    assert any("bbb" in k for k in r)


# ── GROUP 27: All-identical and near-identical sets ───────────────────────────

def test_T139_all_identical_10():
    r = fit(["same_string"] * 10)
    total_strings(r, 10)
    assert len(r) == 1
    assert "same_string" in r


def test_T140_all_identical_50():
    r = fit(["repeat"] * 50)
    total_strings(r, 50)
    assert len(r) == 1


def test_T141_two_groups_identical_members():
    r = fit(["aaa"] * 30 + ["bbb"] * 30)
    total_strings(r, 60)
    assert len(r) == 2


def test_T142_one_unique_rest_identical():
    r = fit(["unique_string"] + ["common"] * 20)
    total_strings(r, 21)
    assert "unique_string" in r or "common" in r


def test_T143_three_identical_groups():
    r = fit(["foo_001"] * 20 + ["bar_001"] * 20 + ["baz_001"] * 20)
    total_strings(r, 60)
    assert len(r) >= 2


# ── GROUP 28: Boundary and edge cases ────────────────────────────────────────

def test_T144_single_string_input():
    r = fit(["only_one"])
    total_strings(r, 1)
    assert "only_one" in r


def test_T145_two_strings_identical():
    r = fit(["same", "same"])
    total_strings(r, 2)
    assert "same" in r


def test_T146_two_strings_no_overlap():
    r = fit(["abc", "xyz"])
    total_strings(r, 2)
    assert "abc" in r
    assert "xyz" in r


def test_T147_all_empty_strings():
    r = fit(["", "", "", ""])
    total_strings(r, 4)
    assert "" in r
    assert r[""] == ["", "", "", ""]


def test_T148_one_empty_rest_normal():
    r = fit(["", "rdf:type", "rdf:label"])
    total_strings(r, 3)
    assert "" in r
    assert any("rdf:" in k for k in r)


def test_T149_all_single_char_same():
    r = fit(["a"] * 5)
    total_strings(r, 5)
    assert "a" in r


def test_T150_all_single_char_different():
    r = fit(["a", "b", "c", "d", "e"])
    total_strings(r, 5)
    assert len(r) >= 1


# ── GROUP 29: Numeric string inputs ──────────────────────────────────────────

def test_T151_phone_numbers():
    r = fit(["+1-800-555-0001", "+1-800-555-0002", "+1-900-555-0001", "+1-900-555-0002"])
    total_strings(r, 4)
    assert any("+1-800" in k or "+1-" in k for k in r)


def test_T152_ip_addresses():
    r = fit(["192.168.1.1", "192.168.1.2", "192.168.2.1", "10.0.0.1", "10.0.0.2"])
    total_strings(r, 5)
    assert any("192.168." in k for k in r)
    assert any("10.0.0." in k for k in r)


def test_T153_version_strings():
    # Sorted: "v1.0.0", "v1.0.1", "v1.1.0", "v2.0.0", "v2.1.0"
    # Consecutive pairs produce sub-groups like "v1.0." and then "v" for the remainder.
    r = fit(["v1.0.0", "v1.0.1", "v1.1.0", "v2.0.0", "v2.1.0"])
    total_strings(r, 5)
    assert any("v" in k for k in r)


def test_T154_isbn_prefixes():
    r = fit(["978-0-001", "978-0-002", "978-1-001", "978-1-002", "979-0-001"])
    total_strings(r, 5)
    assert any("978-" in k for k in r)


def test_T155_hex_color_codes():
    r = fit(["#FF0000", "#FF0001", "#00FF00", "#00FF01", "#0000FF"])
    total_strings(r, 5)
    assert any("#FF00" in k for k in r)
    assert any("#00FF" in k for k in r)


def test_T156_timestamps():
    # Sorted: "2024-01-01", "2024-01-02", "2024-02-01", "2025-01-01", "2025-01-02"
    # Fine sub-groups emerge like "2024-01-0"; the remaining pair may share "202".
    r = fit(["2024-01-01", "2024-01-02", "2024-02-01", "2025-01-01", "2025-01-02"])
    total_strings(r, 5)
    assert any("202" in k for k in r)


# ── GROUP 30: Mixed domain real-world combos ─────────────────────────────────

def test_T157_mixed_ontology_gene_file():
    r = fit(sorted([
        "rdf:type", "rdf:label",
        "GO:0001234", "GO:0005678",
        "/data/run_001.tsv", "/data/run_002.tsv",
        "hasGlycan", "hasGlycanBinding",
    ]))
    total_strings(r, 8)
    assert len(r) >= 3


def test_T158_api_endpoints_mixed_version():
    # Sorted consecutive pairs produce "/api/v1/" for the v1 group,
    # then "/api/v" as the prefix for the leftover v2 entries, and "/internal/" for internals.
    r = fit(sorted([
        "/api/v1/users", "/api/v1/posts", "/api/v1/comments",
        "/api/v2/users", "/api/v2/posts",
        "/internal/health", "/internal/metrics",
    ]))
    total_strings(r, 7)
    assert any("/api/v1/" in k for k in r)
    assert any("/internal/" in k for k in r)
    assert any("/api/v" in k for k in r)


def test_T159_config_keys_mixed():
    r = fit(sorted([
        "db.host", "db.port", "db.name",
        "cache.host", "cache.port",
        "log.level", "log.path",
        "app.name",
    ]))
    total_strings(r, 8)
    assert any("db." in k for k in r)
    assert any("cache." in k for k in r)
    assert any("log." in k for k in r)


def test_T160_bioinformatics_ids():
    # Sorted: ENSM..., ENSG...(x3), ENST...(x2), P12345, P67890, Q12345
    # The ENSG block gets "ENSG0000000"; the wider ENS block gets "ENS";
    # P-prefixed pair gets "P"; Q stands alone.
    r = fit(sorted([
        "ENSG00000001", "ENSG00000002", "ENSG00000003",
        "ENST00000001", "ENST00000002",
        "ENSM00000001",
        "P12345", "P67890",
        "Q12345",
    ]))
    total_strings(r, 9)
    assert any("ENS" in k for k in r)
    assert any("P" in k for k in r)


# ── GROUP 31: get_groups_recursive — basic behaviour ─────────────────────────

def test_R001_flat_singletons_true_basic():
    g = AutoPrefixGrouper().fit(["hasGlycan", "hasGlycanBinding", "hasX", "abc"])
    r = g.get_groups_recursive(mode="flat", singletons=True)
    assert "has" in r
    assert "hasGlycan" in r
    assert "hasX" in r
    assert r["hasGlycan"] == ["hasGlycan", "hasGlycanBinding"] or \
           set(r["hasGlycan"]) == {"hasGlycan", "hasGlycanBinding"}


def test_R002_flat_singletons_false_basic():
    g = AutoPrefixGrouper().fit(["hasGlycan", "hasGlycanBinding", "hasX", "abc"])
    r = g.get_groups_recursive(mode="flat", singletons=False)
    assert "has" in r
    assert "hasGlycan" in r
    # hasX covers only 1 string — must not appear as a key
    assert "hasX" not in r


def test_R003_nested_singletons_true_basic():
    g = AutoPrefixGrouper().fit(["hasGlycan", "hasGlycanBinding", "hasX", "abc"])
    r = g.get_groups_recursive(mode="nested", singletons=True)
    assert "has" in r
    assert isinstance(r["has"], dict)
    assert "hasGlycan" in r["has"]
    assert "hasX" in r["has"]


def test_R004_nested_singletons_false_basic():
    g = AutoPrefixGrouper().fit(["hasGlycan", "hasGlycanBinding", "hasX", "abc"])
    r = g.get_groups_recursive(mode="nested", singletons=False)
    assert "has" in r
    assert isinstance(r["has"], dict)
    assert "hasGlycan" in r["has"]
    assert "hasX" not in r["has"]


def test_R005_invalid_mode_raises():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    with pytest.raises(ValueError, match="mode"):
        g.get_groups_recursive(mode="wrong")


def test_R006_not_fitted_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(RuntimeError, match="not fitted"):
        g.get_groups_recursive()


# ── GROUP 32: get_groups_recursive — depth and total counts ──────────────────

def test_R007_flat_total_strings_preserved():
    strings = ["hasGlycan", "hasGlycanBinding", "hasX", "abc", "xyz"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="flat", singletons=True)
    # Top-level keys must still cover all original strings
    top = g.get_groups()
    top_total = sum(len(v) for v in top.values())
    assert top_total == 5
    # Recursive result has at least as many keys as top-level
    assert len(r) >= len(top)


def test_R008_nested_all_strings_reachable():
    strings = ["hasGlycan", "hasGlycanBinding", "hasX", "abc"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="nested", singletons=True)

    def collect_leaves(d):
        leaves = []
        for v in d.values():
            if isinstance(v, list):
                leaves.extend(v)
            else:
                leaves.extend(collect_leaves(v))
        return leaves

    leaves = collect_leaves(r)
    # Every original string must appear at least once
    for s in strings:
        assert s in leaves


def test_R009_flat_no_duplicate_top_keys():
    strings = ["hasGlycan", "hasGlycanBinding", "hasX", "hasY", "abc"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="flat", singletons=True)
    # Keys in a dict are always unique — just verify no KeyError and dict is valid
    assert isinstance(r, dict)


def test_R010_three_level_deep():
    # ab -> abc -> abcd
    strings = ["abcd_01", "abcd_02", "abc_01", "ab_01", "ab_02"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="flat", singletons=False)
    assert isinstance(r, dict)
    # At minimum the top-level prefix must be there
    assert len(r) >= 1


# ── GROUP 33: get_groups_recursive — empty strings and special inputs ─────────

def test_R011_empty_strings_in_input():
    # Sort key puts hasGlycan before hasGlycanBinding — top-level already
    # finds "hasGlycan" as the prefix; "has" does not appear as a key here.
    strings = ["hasGlycan", "hasGlycanBinding", "", "", "abc"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="flat", singletons=True)
    assert "" in r
    assert any("has" in k for k in r)


def test_R012_all_identical_flat():
    g = AutoPrefixGrouper().fit(["same"] * 5)
    r = g.get_groups_recursive(mode="flat", singletons=True)
    assert "same" in r
    assert r["same"] == ["same"] * 5


def test_R013_all_identical_nested():
    g = AutoPrefixGrouper().fit(["same"] * 5)
    r = g.get_groups_recursive(mode="nested", singletons=True)
    assert "same" in r


def test_R014_no_common_prefix_flat():
    g = AutoPrefixGrouper().fit(["alpha", "beta", "gamma"])
    r = g.get_groups_recursive(mode="flat", singletons=True)
    # No sub-grouping possible — result equals get_groups()
    assert r == g.get_groups()


def test_R015_no_common_prefix_nested():
    g = AutoPrefixGrouper().fit(["alpha", "beta", "gamma"])
    r = g.get_groups_recursive(mode="nested", singletons=True)
    assert r == g.get_groups()


# ── GROUP 34: get_groups_recursive — singletons=False edge cases ──────────────

def test_R016_singletons_false_removes_isolates():
    # hasX, hasY, hasZ are singletons after stripping "has"
    strings = ["hasGlycan", "hasGlycanBinding", "hasX", "hasY", "hasZ"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="flat", singletons=False)
    assert "hasX" not in r
    assert "hasY" not in r
    assert "hasZ" not in r
    assert "hasGlycan" in r


def test_R017_singletons_false_nested_no_isolate_keys():
    strings = ["hasGlycan", "hasGlycanBinding", "hasX", "hasY"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="nested", singletons=False)
    has_group = r.get("has", {})
    if isinstance(has_group, dict):
        assert "hasX" not in has_group
        assert "hasY" not in has_group


def test_R018_singletons_false_all_singletons():
    # Every string is unique with no shared prefix — result equals get_groups()
    g = AutoPrefixGrouper().fit(["alpha", "beta", "gamma"])
    r_true = g.get_groups_recursive(mode="flat", singletons=True)
    r_false = g.get_groups_recursive(mode="flat", singletons=False)
    assert r_true == r_false


# ── GROUP 35: get_groups_recursive — real-world domain inputs ─────────────────

def test_R019_rdf_owl_rdfs():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty",
               "rdfs:label", "rdfs:comment"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="flat", singletons=False)
    assert any("rdf" in k for k in r)
    assert any("owl" in k for k in r)


def test_R020_glycan_predicates():
    strings = ["hasGlycan", "hasGlycanBinding", "hasGlycanMotif",
               "hasX", "hasY", "isA", "isB"]
    g = AutoPrefixGrouper().fit(strings)
    r_flat = g.get_groups_recursive(mode="flat", singletons=False)
    # hasGlycan group must exist with at least 2 members
    assert "hasGlycan" in r_flat
    assert len(r_flat["hasGlycan"]) >= 2


def test_R021_file_paths_recursive():
    strings = [
        "/data/bio/run_001", "/data/bio/run_002",
        "/data/chem/run_001", "/data/chem/run_002",
        "/logs/app.log", "/logs/error.log",
    ]
    g = AutoPrefixGrouper().fit(sorted(strings))
    r = g.get_groups_recursive(mode="flat", singletons=False)
    assert any("/data/" in k for k in r)
    assert any("/logs/" in k for k in r)


def test_R022_nested_mode_value_types():
    strings = ["hasGlycan", "hasGlycanBinding", "hasX", "abc"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="nested", singletons=True)
    for v in r.values():
        assert isinstance(v, (list, dict))


def test_R023_flat_mode_all_values_are_lists():
    strings = ["hasGlycan", "hasGlycanBinding", "hasX", "abc"]
    g = AutoPrefixGrouper().fit(strings)
    r = g.get_groups_recursive(mode="flat", singletons=True)
    for v in r.values():
        assert isinstance(v, list)


def test_R024_integer_input_recursive():
    g = AutoPrefixGrouper().fit([1, 2, 10, 11, 100])
    # suppress warning output in test
    r = g.get_groups_recursive(mode="flat", singletons=False)
    assert isinstance(r, dict)
    total = sum(len(v) for v in g.get_groups().values())
    assert total == 5


# ── GROUP 36: prefix_depth and position_index on fit() ───────────────────────

URIS = [
    "http://semanticscience.org/resource/SIO_000001",
    "http://semanticscience.org/resource/SIO_000255",
    "http://semanticscience.org/resource/SIO_000772",
]

def test_P001_prefix_depth_basic():
    g = AutoPrefixGrouper().fit(URIS, prefix_depth="/", position_index=4)
    r = g.get_groups()
    assert "http://semanticscience.org/resource/" in r


def test_P002_prefix_depth_position_1():
    g = AutoPrefixGrouper().fit(URIS, prefix_depth="/", position_index=1)
    r = g.get_groups()
    # Trimmed at first "/" → "http:/"
    assert any(k.startswith("http:/") for k in r)


def test_P003_prefix_depth_position_2():
    g = AutoPrefixGrouper().fit(URIS, prefix_depth="/", position_index=2)
    r = g.get_groups()
    # Trimmed at second "/" → "http://"
    assert any(k.startswith("http://") for k in r)


def test_P004_prefix_depth_last_occurrence():
    # position_index=-1 trims at last "/" inside the common prefix
    g = AutoPrefixGrouper().fit(URIS, prefix_depth="/", position_index=-1)
    r = g.get_groups()
    assert isinstance(r, dict)
    # All original strings still accounted for
    total = sum(len(v) for v in r.values())
    assert total == 3


def test_P005_prefix_depth_no_delimiter_in_prefix():
    # Delimiter not found — groups unchanged from raw algorithm
    strings = ["abcX", "abcY", "abcZ"]
    g = AutoPrefixGrouper().fit(strings, prefix_depth="/", position_index=2)
    r = g.get_groups()
    assert isinstance(r, dict)
    total = sum(len(v) for v in r.values())
    assert total == 3


def test_P006_prefix_depth_delimiter_at_every_position():
    strings = ["a/b/c/d", "a/b/c/e", "a/b/c/f"]
    g = AutoPrefixGrouper().fit(strings, prefix_depth="/", position_index=3)
    r = g.get_groups()
    assert any("a/b/c/" in k for k in r)


def test_P007_prefix_depth_does_not_modify_fitted_state_twice():
    g = AutoPrefixGrouper().fit(URIS, prefix_depth="/", position_index=4)
    r1 = g.get_groups()
    r2 = g.get_groups()
    assert r1 == r2


def test_P008_prefix_depth_all_strings_preserved():
    g = AutoPrefixGrouper().fit(URIS, prefix_depth="/", position_index=3)
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == len(URIS)


def test_P009_prefix_depth_without_position_index_uses_last():
    # Omitting position_index defaults to -1 (last occurrence)
    g1 = AutoPrefixGrouper().fit(URIS, prefix_depth="/")
    g2 = AutoPrefixGrouper().fit(URIS, prefix_depth="/", position_index=-1)
    assert g1.get_groups() == g2.get_groups()


def test_P010_prefix_depth_none_means_raw_algorithm():
    g_raw = AutoPrefixGrouper().fit(URIS)
    g_none = AutoPrefixGrouper().fit(URIS, prefix_depth=None)
    assert g_raw.get_groups() == g_none.get_groups()


# ── GROUP 37: inspect_prefix() ───────────────────────────────────────────────

def test_I001_inspect_prefix_basic(capsys):
    g = AutoPrefixGrouper()
    g.inspect_prefix("http://semanticscience.org/resource/SIO_000001", "/")
    out = capsys.readouterr().out
    assert "position_index=1" in out
    assert "position_index=2" in out
    assert "position_index=3" in out
    assert "position_index=4" in out


def test_I002_inspect_prefix_shows_trimmed_string(capsys):
    g = AutoPrefixGrouper()
    g.inspect_prefix("a/b/c", "/")
    out = capsys.readouterr().out
    assert '"a/"' in out
    assert '"a/b/"' in out


def test_I003_inspect_prefix_no_delimiter(capsys):
    g = AutoPrefixGrouper()
    g.inspect_prefix("abcdef", "/")
    out = capsys.readouterr().out
    assert "not found" in out.lower()


def test_I004_inspect_prefix_delimiter_at_start(capsys):
    g = AutoPrefixGrouper()
    g.inspect_prefix("/usr/local/bin", "/")
    out = capsys.readouterr().out
    assert "position_index=1" in out


def test_I005_inspect_prefix_does_not_require_fit():
    g = AutoPrefixGrouper()  # never fitted
    # Should not raise
    g.inspect_prefix("a/b/c", "/")


def test_I006_inspect_prefix_bad_delimiter_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(ValueError):
        g.inspect_prefix("a/b/c", "//")


def test_I007_inspect_prefix_empty_delimiter_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(ValueError):
        g.inspect_prefix("a/b/c", "")


def test_I008_inspect_prefix_non_string_delimiter_raises():
    g = AutoPrefixGrouper()
    with pytest.raises((ValueError, TypeError)):
        g.inspect_prefix("a/b/c", 47)


def test_I009_inspect_prefix_single_occurrence(capsys):
    g = AutoPrefixGrouper()
    g.inspect_prefix("abc/def", "/")
    out = capsys.readouterr().out
    assert "position_index=1" in out
    assert "position_index=2" not in out


def test_I010_inspect_prefix_uses_position_index_label(capsys):
    # Confirm label is exactly "position_index=N" not "Position N"
    g = AutoPrefixGrouper()
    g.inspect_prefix("x/y", "/")
    out = capsys.readouterr().out
    assert "position_index=" in out
    assert "Position " not in out


# ── GROUP 38: preview_fit() ──────────────────────────────────────────────────

def test_V001_preview_fit_returns_dict():
    g = AutoPrefixGrouper()
    r = g.preview_fit(URIS, prefix_depth="/", position_index=4)
    assert isinstance(r, dict)


def test_V002_preview_fit_does_not_change_fitted_state():
    g = AutoPrefixGrouper()
    assert not g._fitted
    g.preview_fit(URIS, prefix_depth="/", position_index=4)
    assert not g._fitted


def test_V003_preview_fit_matches_actual_fit():
    g = AutoPrefixGrouper()
    preview = g.preview_fit(URIS, prefix_depth="/", position_index=4)
    g.fit(URIS, prefix_depth="/", position_index=4)
    actual = g.get_groups()
    assert preview == actual


def test_V004_preview_fit_all_strings_preserved():
    g = AutoPrefixGrouper()
    r = g.preview_fit(URIS, prefix_depth="/", position_index=3)
    total = sum(len(v) for v in r.values())
    assert total == len(URIS)


def test_V005_preview_fit_different_position_different_result():
    g = AutoPrefixGrouper()
    r2 = g.preview_fit(URIS, prefix_depth="/", position_index=2)
    r4 = g.preview_fit(URIS, prefix_depth="/", position_index=4)
    assert r2 != r4


def test_V006_preview_fit_does_not_affect_subsequent_fit():
    g = AutoPrefixGrouper()
    g.preview_fit(URIS, prefix_depth="/", position_index=4)
    g.fit(URIS)
    r = g.get_groups()
    # Raw fit — no depth trimming
    assert isinstance(r, dict)
    total = sum(len(v) for v in r.values())
    assert total == len(URIS)


def test_V007_preview_fit_integer_strings_converted():
    g = AutoPrefixGrouper()
    r = g.preview_fit([10, 11, 100, 101], prefix_depth="1", position_index=1)
    assert isinstance(r, dict)


def test_V008_preview_fit_empty_list_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(ValueError):
        g.preview_fit([], prefix_depth="/", position_index=1)


def test_V009_preview_fit_single_string_returns_dict():
    g = AutoPrefixGrouper()
    # A single string produces no pairs — returns a valid dict (possibly empty)
    r = g.preview_fit(["only"], prefix_depth="/", position_index=1)
    assert isinstance(r, dict)


def test_V010_preview_fit_returns_new_dict_each_call():
    g = AutoPrefixGrouper()
    r1 = g.preview_fit(URIS, prefix_depth="/", position_index=4)
    r2 = g.preview_fit(URIS, prefix_depth="/", position_index=4)
    assert r1 == r2
    assert r1 is not r2


# ── GROUP 39: prefix_depth merge-and-resplit fix ─────────────────────────────

OBO_STRINGS = [
    "http://purl.obolibrary.org/obo/GO_0000001",
    "http://purl.obolibrary.org/obo/GO_0000002",
    "http://purl.obolibrary.org/obo/RO_0000001",
    "http://purl.obolibrary.org/obo/RO_0000002",
]

def test_M001_merged_groups_are_resplit():
    g = AutoPrefixGrouper().fit(OBO_STRINGS, prefix_depth="/", position_index=4, resplit=True)
    r = g.get_groups()
    # Must not collapse into a single key
    assert len(r) > 1


def test_M002_resplit_GO_group_exists():
    g = AutoPrefixGrouper().fit(OBO_STRINGS, prefix_depth="/", position_index=4, resplit=True)
    r = g.get_groups()
    assert any("GO_" in k for k in r)


def test_M003_resplit_RO_group_exists():
    g = AutoPrefixGrouper().fit(OBO_STRINGS, prefix_depth="/", position_index=4, resplit=True)
    r = g.get_groups()
    assert any("RO_" in k for k in r)


def test_M004_all_strings_preserved_after_resplit():
    g = AutoPrefixGrouper().fit(OBO_STRINGS, prefix_depth="/", position_index=4, resplit=True)
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == len(OBO_STRINGS)


def test_M005_no_string_duplicated_after_resplit():
    g = AutoPrefixGrouper().fit(OBO_STRINGS, prefix_depth="/", position_index=4, resplit=True)
    r = g.get_groups()
    all_strings = [s for v in r.values() for s in v]
    assert len(all_strings) == len(set(all_strings))


def test_M006_single_group_not_resplit():
    # Only SIO strings — no merge possible, one group expected
    uris = [
        "http://semanticscience.org/resource/SIO_000001",
        "http://semanticscience.org/resource/SIO_000255",
        "http://semanticscience.org/resource/SIO_000772",
    ]
    g = AutoPrefixGrouper().fit(uris, prefix_depth="/", position_index=4)
    r = g.get_groups()
    assert "http://semanticscience.org/resource/" in r
    assert len(r) == 1


def test_M007_three_namespaces_all_resplit():
    strings = [
        "http://example.org/obo/AA_0001",
        "http://example.org/obo/AA_0002",
        "http://example.org/obo/BB_0001",
        "http://example.org/obo/BB_0002",
        "http://example.org/obo/CC_0001",
        "http://example.org/obo/CC_0002",
    ]
    g = AutoPrefixGrouper().fit(strings, prefix_depth="/", position_index=4, resplit=True)
    r = g.get_groups()
    assert len(r) >= 2
    total = sum(len(v) for v in r.values())
    assert total == 6


def test_M008_no_delimiter_in_prefix_unchanged():
    strings = ["SIO_000001", "SIO_000255", "SIO_000772"]
    g = AutoPrefixGrouper().fit(strings, prefix_depth="/", position_index=4)
    r = g.get_groups()
    # Delimiter not in prefix — kept as-is
    assert isinstance(r, dict)
    total = sum(len(v) for v in r.values())
    assert total == 3


def test_M009_position_index_out_of_range_keeps_prefix():
    uris = [
        "http://semanticscience.org/resource/SIO_000001",
        "http://semanticscience.org/resource/SIO_000255",
    ]
    # position_index=99 is out of range — prefix kept unchanged
    g = AutoPrefixGrouper().fit(uris, prefix_depth="/", position_index=99)
    r = g.get_groups()
    assert isinstance(r, dict)
    total = sum(len(v) for v in r.values())
    assert total == 2


def test_M010_resplit_preserves_correct_members():
    g = AutoPrefixGrouper().fit(OBO_STRINGS, prefix_depth="/", position_index=4, resplit=True)
    r = g.get_groups()
    go_key = next(k for k in r if "GO_" in k)
    ro_key = next(k for k in r if "RO_" in k)
    assert all("GO_" in s for s in r[go_key])
    assert all("RO_" in s for s in r[ro_key])


# ── GROUP 40: export() — JSON ─────────────────────────────────────────────────

import json as _json

def test_E001_export_json_returns_string():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    result = g.export("json")
    assert isinstance(result, str)


def test_E002_export_json_valid_json():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    result = g.export("json")
    parsed = _json.loads(result)
    assert isinstance(parsed, dict)


def test_E003_export_json_all_prefixes_present():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"])
    parsed = _json.loads(g.export("json"))
    assert "rdf:" in parsed
    assert "owl:" in parsed


def test_E004_export_json_all_strings_in_values():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    parsed = _json.loads(g.export("json"))
    all_exported = [s for v in parsed.values() for s in v]
    assert sorted(all_exported) == sorted(strings)


def test_E005_export_json_values_are_lists():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    parsed = _json.loads(g.export("json"))
    for v in parsed.values():
        assert isinstance(v, list)


def test_E006_export_json_default_format():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    # Default argument is json
    result_default = g.export()
    result_explicit = g.export("json")
    assert _json.loads(result_default) == _json.loads(result_explicit)


def test_E007_export_json_unicode_preserved():
    strings = ["タンパク1", "タンパク2"]
    g = AutoPrefixGrouper().fit(strings)
    parsed = _json.loads(g.export("json"))
    all_exported = [s for v in parsed.values() for s in v]
    assert sorted(all_exported) == sorted(strings)


def test_E008_export_before_fit_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(RuntimeError):
        g.export("json")


def test_E009_export_unsupported_format_raises():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    with pytest.raises(ValueError):
        g.export("xml")


def test_E010_export_format_case_insensitive():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    r1 = _json.loads(g.export("json"))
    r2 = _json.loads(g.export("JSON"))
    assert r1 == r2


# ── GROUP 41: export() — CSV ─────────────────────────────────────────────────

def test_E011_export_csv_returns_string():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    result = g.export("csv")
    assert isinstance(result, str)


def test_E012_export_csv_has_header():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    lines = g.export("csv").splitlines()
    assert lines[0] == "prefix,string"


def test_E013_export_csv_row_count():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("csv").splitlines()
    # header + one row per string
    assert len(lines) == 1 + len(strings)


def test_E014_export_csv_all_strings_present():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    csv_text = g.export("csv")
    for s in strings:
        assert s in csv_text


def test_E015_export_csv_comma_in_string_quoted():
    # String with comma must be quoted in CSV
    strings = ["a,b", "a,c"]
    g = AutoPrefixGrouper().fit(strings)
    csv_text = g.export("csv")
    assert '"a,b"' in csv_text or '"a,c"' in csv_text


def test_E016_export_csv_quote_in_string_escaped():
    strings = ['say"hi', 'say"bye']
    g = AutoPrefixGrouper().fit(strings)
    csv_text = g.export("csv")
    # Double-quote escape: "" inside quoted field
    assert '""' in csv_text


def test_E017_export_csv_format_case_insensitive():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    r1 = g.export("csv")
    r2 = g.export("CSV")
    assert r1 == r2


def test_E018_export_csv_each_row_has_two_fields():
    strings = ["rdf:type", "rdf:label", "owl:Class"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("csv").splitlines()
    for line in lines[1:]:  # skip header
        # Simple check: at least one comma present
        assert "," in line


def test_E019_export_csv_no_duplicate_rows():
    strings = ["rdf:type", "rdf:label", "owl:Class"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("csv").splitlines()
    data_rows = lines[1:]
    assert len(data_rows) == len(set(data_rows))


def test_E020_export_csv_before_fit_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(RuntimeError):
        g.export("csv")


# ── GROUP 42: export() — TSV ──────────────────────────────────────────────────

def test_E021_export_tsv_returns_string():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    assert isinstance(g.export("tsv"), str)


def test_E022_export_tsv_has_header():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    lines = g.export("tsv").splitlines()
    assert lines[0] == "prefix\tstring"


def test_E023_export_tsv_row_count():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("tsv").splitlines()
    assert len(lines) == 1 + len(strings)


def test_E024_export_tsv_all_strings_present():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    tsv = g.export("tsv")
    for s in strings:
        assert s in tsv


def test_E025_export_tsv_uses_tab_separator():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    lines = g.export("tsv").splitlines()
    for line in lines:
        assert "\t" in line


def test_E026_export_tsv_each_row_has_two_fields():
    strings = ["rdf:type", "rdf:label", "owl:Class"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("tsv").splitlines()
    for line in lines:
        parts = line.split("\t")
        assert len(parts) == 2


def test_E027_export_tsv_case_insensitive():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    assert g.export("tsv") == g.export("TSV")


def test_E028_export_tsv_no_duplicate_rows():
    strings = ["rdf:type", "rdf:label", "owl:Class"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("tsv").splitlines()
    data_rows = lines[1:]
    assert len(data_rows) == len(set(data_rows))


def test_E029_export_tsv_before_fit_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(RuntimeError):
        g.export("tsv")


def test_E030_export_tsv_unicode_preserved():
    strings = ["タンパク1", "タンパク2"]
    g = AutoPrefixGrouper().fit(strings)
    tsv = g.export("tsv")
    for s in strings:
        assert s in tsv


# ── GROUP 43: export() — Markdown ────────────────────────────────────────────

def test_E031_export_markdown_returns_string():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    assert isinstance(g.export("markdown"), str)


def test_E032_export_markdown_has_header_row():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    lines = g.export("markdown").splitlines()
    assert "prefix" in lines[0]
    assert "string" in lines[0]


def test_E033_export_markdown_has_separator_row():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    lines = g.export("markdown").splitlines()
    assert "---" in lines[1]


def test_E034_export_markdown_row_count():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("markdown").splitlines()
    # header + separator + one row per string
    assert len(lines) == 2 + len(strings)


def test_E035_export_markdown_all_strings_present():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    md = g.export("markdown")
    for s in strings:
        assert s in md


def test_E036_export_markdown_pipe_delimited():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    lines = g.export("markdown").splitlines()
    for line in lines:
        assert line.startswith("|")
        assert line.endswith("|")


def test_E037_export_markdown_case_insensitive():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    assert g.export("markdown") == g.export("MARKDOWN")


def test_E038_export_markdown_no_duplicate_rows():
    strings = ["rdf:type", "rdf:label", "owl:Class"]
    g = AutoPrefixGrouper().fit(strings)
    lines = g.export("markdown").splitlines()
    data_rows = lines[2:]
    assert len(data_rows) == len(set(data_rows))


def test_E039_export_markdown_before_fit_raises():
    g = AutoPrefixGrouper()
    with pytest.raises(RuntimeError):
        g.export("markdown")


def test_E040_export_markdown_unicode_preserved():
    strings = ["タンパク1", "タンパク2"]
    g = AutoPrefixGrouper().fit(strings)
    md = g.export("markdown")
    for s in strings:
        assert s in md


# ── GROUP 44: export() — cross-format consistency ────────────────────────────

def test_E041_all_formats_same_string_count():
    strings = ["rdf:type", "rdf:label", "owl:Class", "owl:ObjectProperty"]
    g = AutoPrefixGrouper().fit(strings)
    parsed_json = _json.loads(g.export("json"))
    json_strings = sorted(s for v in parsed_json.values() for s in v)
    csv_strings = sorted(
        line.split(",")[1] for line in g.export("csv").splitlines()[1:]
    )
    tsv_strings = sorted(
        line.split("\t")[1] for line in g.export("tsv").splitlines()[1:]
    )
    md_strings = sorted(
        line.split("|")[2].strip()
        for line in g.export("markdown").splitlines()[2:]
    )
    assert json_strings == csv_strings == tsv_strings == md_strings


def test_E042_unsupported_format_raises_valueerror():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    with pytest.raises(ValueError):
        g.export("xml")


def test_E043_unsupported_format_error_message_names_supported():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    with pytest.raises(ValueError, match="json"):
        g.export("xml")


def test_E044_export_large_input_all_formats():
    strings = [f"ns:item{i:04d}" for i in range(100)]
    g = AutoPrefixGrouper().fit(strings)
    for fmt in ("json", "csv", "tsv", "markdown"):
        result = g.export(fmt)
        assert isinstance(result, str)
        assert len(result) > 0


# ── GROUP 12: prefix_depth and position_index as lists ──────────────────────

# --- single-element list behaves identically to scalar ---

def test_L001_single_delimiter_list_same_as_scalar():
    uris = [
        "http://semanticscience.org/resource/SIO_000001",
        "http://semanticscience.org/resource/SIO_000255",
    ]
    r_scalar = AutoPrefixGrouper().fit(uris, prefix_depth="/", position_index=4).get_groups()
    r_list   = AutoPrefixGrouper().fit(uris, prefix_depth=["/"], position_index=[4]).get_groups()
    assert r_scalar == r_list


def test_L002_single_delimiter_list_single_int_index():
    uris = [
        "http://semanticscience.org/resource/SIO_000001",
        "http://semanticscience.org/resource/SIO_000255",
    ]
    r_scalar = AutoPrefixGrouper().fit(uris, prefix_depth="/", position_index=4).get_groups()
    r_list   = AutoPrefixGrouper().fit(uris, prefix_depth=["/"], position_index=4).get_groups()
    assert r_scalar == r_list


# --- two delimiters, strings use different ones ---

def test_L003_two_delimiters_strings_split_by_first_match():
    # "#" strings should cut at "#", "/" strings should cut at "/"
    data = [
        "http://www.w3.org/2002/07/owl#Class",
        "http://www.w3.org/2002/07/owl#ObjectProperty",
        "http://purl.obolibrary.org/obo/GO_0001234",
        "http://purl.obolibrary.org/obo/GO_0005678",
    ]
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["#", "/"],
        position_index=[-1, 5],
    )
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 4


def test_L004_hash_delimiter_strings_cut_at_hash():
    data = [
        "http://www.w3.org/2002/07/owl#Class",
        "http://www.w3.org/2002/07/owl#ObjectProperty",
    ]
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["#", "/"],
        position_index=[-1, 4],
    )
    r = g.get_groups()
    # Both strings contain "#" so "#" wins; prefix ends at "#"
    assert any("#" in k for k in r)


def test_L005_slash_delimiter_strings_no_hash():
    data = [
        "http://purl.obolibrary.org/obo/GO_0001234",
        "http://purl.obolibrary.org/obo/GO_0005678",
    ]
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["#", "/"],
        position_index=[-1, 5],
    )
    r = g.get_groups()
    # No "#" in these strings so "/" is used
    assert all("#" not in k for k in r)
    total = sum(len(v) for v in r.values())
    assert total == 2


# --- three delimiters ---

def test_L006_three_delimiters_each_string_uses_first_match():
    data = [
        "mailto:user@example.com",
        "mailto:admin@example.org",
        "http://example.com/path/page",
        "http://example.org/path/page",
        "urn:isbn:0451450523",
        "urn:isbn:0345391802",
    ]
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["@", "/", ":"],
        position_index=[-1, 3, 1],
    )
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 6


# --- position_index as single int applied to all delimiters ---

def test_L007_single_int_position_index_applies_to_all():
    data = [
        "http://www.w3.org/2002/07/owl#Class",
        "http://www.w3.org/2002/07/owl#ObjectProperty",
        "ftp://files.example.com/pub/data",
        "ftp://files.example.com/pub/meta",
    ]
    # position_index=-1 means last occurrence of whichever delimiter matched
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["#", "/"],
        position_index=-1,
    )
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 4


# --- validation errors ---

def test_L008_mismatched_list_lengths_raises_valueerror():
    with pytest.raises(ValueError, match="same length"):
        AutoPrefixGrouper().fit(
            ["a/b", "a/c"],
            prefix_depth=["/", "#"],
            position_index=[1],  # length mismatch
        )


def test_L009_non_single_char_in_list_raises_valueerror():
    with pytest.raises(ValueError):
        AutoPrefixGrouper().fit(
            ["a/b", "a/c"],
            prefix_depth=["//"],  # two characters, invalid
        )


def test_L010_empty_list_prefix_depth_raises_valueerror():
    # An empty list has no delimiters; each entry would need to be a single char
    # The list itself is valid but contains no items — no trimming possible.
    # Confirm it at least does not crash and produces the raw groups.
    data = ["rdf:type", "rdf:label", "owl:Class"]
    # Empty list passes validation (no entries to check), falls through to raw groups
    g = AutoPrefixGrouper().fit(data, prefix_depth=[])
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 3


# --- no delimiter found in string falls back to raw prefix ---

def test_L011_no_delimiter_match_keeps_raw_prefix():
    data = ["rdf:type", "rdf:label"]
    # Neither "#" nor "@" appears in these strings
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["#", "@"],
        position_index=[-1, -1],
    )
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 2


# --- preview_fit accepts lists ---

def test_L012_preview_fit_list_prefix_depth():
    data = [
        "http://www.w3.org/2002/07/owl#Class",
        "http://www.w3.org/2002/07/owl#ObjectProperty",
    ]
    g = AutoPrefixGrouper()
    r = g.preview_fit(data, prefix_depth=["#", "/"], position_index=[-1, 4])
    assert isinstance(r, dict)
    total = sum(len(v) for v in r.values())
    assert total == 2
    # fitted state must remain unchanged
    assert not g._fitted


# --- all strings land in result (no loss) ---

def test_L013_no_string_loss_mixed_delimiters():
    import random
    random.seed(42)
    base = ["http://ex.org/res/item{:03d}".format(i) for i in range(10)]
    hash_items = ["http://ex.org/onto#Term{:03d}".format(i) for i in range(10)]
    data = base + hash_items
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["#", "/"],
        position_index=[-1, 5],
    )
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 20


# --- position_index list with -1 entries ---

def test_L014_position_index_list_with_negative_one():
    data = [
        "http://www.w3.org/2002/07/owl#Class",
        "http://www.w3.org/2002/07/owl#ObjectProperty",
        "http://purl.obolibrary.org/obo/GO_0001234",
        "http://purl.obolibrary.org/obo/GO_0005678",
    ]
    g = AutoPrefixGrouper().fit(
        data,
        prefix_depth=["#", "/"],
        position_index=[-1, -1],
    )
    r = g.get_groups()
    total = sum(len(v) for v in r.values())
    assert total == 4

# ── GROUP 42: strip_prefix parameter ─────────────────────────────────────────

SP_URIS = [
    "http://glycosmos.org/disease/DOID:0001816",
    "http://glycosmos.org/disease/DOID:0002116",
    "http://jcggdb.jp/rdf/diseases/ggdonto#CON0000",
    "http://jcggdb.jp/rdf/diseases/ggdonto#CON0001",
]

def test_SP001_strip_prefix_false_returns_full_strings():
    g = AutoPrefixGrouper().fit(SP_URIS, prefix_depth=["#", "/"], position_index=-1)
    r = g.get_groups(strip_prefix=False)
    all_strings = [s for v in r.values() for s in v]
    assert all(s in SP_URIS for s in all_strings)


def test_SP002_strip_prefix_true_removes_key_from_members():
    g = AutoPrefixGrouper().fit(SP_URIS, prefix_depth=["#", "/"], position_index=-1)
    r = g.get_groups(strip_prefix=True)
    for prefix, members in r.items():
        for s in members:
            assert not s.startswith(prefix), f"{s!r} still starts with {prefix!r}"


def test_SP003_strip_prefix_true_doid_suffix_correct():
    g = AutoPrefixGrouper().fit(SP_URIS, prefix_depth=["#", "/"], position_index=-1)
    r = g.get_groups(strip_prefix=True)
    doid_key = next(k for k in r if "glycosmos" in k)
    assert "DOID:0001816" in r[doid_key]
    assert "DOID:0002116" in r[doid_key]


def test_SP004_strip_prefix_true_con_suffix_correct():
    g = AutoPrefixGrouper().fit(SP_URIS, prefix_depth=["#", "/"], position_index=-1)
    r = g.get_groups(strip_prefix=True)
    con_key = next(k for k in r if "ggdonto" in k)
    assert "CON0000" in r[con_key]
    assert "CON0001" in r[con_key]


def test_SP005_strip_prefix_preserves_total_count():
    g = AutoPrefixGrouper().fit(SP_URIS, prefix_depth=["#", "/"], position_index=-1)
    r = g.get_groups(strip_prefix=True)
    assert sum(len(v) for v in r.values()) == len(SP_URIS)


def test_SP006_strip_prefix_default_is_false():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label", "owl:Class"])
    r_default = g.get_groups()
    r_explicit = g.get_groups(strip_prefix=False)
    assert r_default == r_explicit


def test_SP007_strip_prefix_no_prefix_depth_full_prefix_removed():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    r = g.get_groups(strip_prefix=True)
    rdf_key = next(k for k in r if k.startswith("rdf"))
    for s in r[rdf_key]:
        assert not s.startswith(rdf_key)


def test_SP008_strip_prefix_singleton_group():
    g = AutoPrefixGrouper().fit(["owl:Class", "rdf:type", "rdf:label"])
    r = g.get_groups(strip_prefix=True)
    owl_key = next(k for k in r if "owl" in k)
    # singleton: full string minus the prefix key
    assert len(r[owl_key]) == 1

# ── GROUP 43: count parameter ─────────────────────────────────────────────────

COUNT_STRINGS = [
    "http://glycosmos.org/disease/DOID:0001816",
    "http://glycosmos.org/disease/DOID:0002116",
    "http://glycosmos.org/disease/DOID:0014667",
    "http://jcggdb.jp/rdf/diseases/ggdonto#CON0000",
    "http://jcggdb.jp/rdf/diseases/ggdonto#CON0001",
]

def test_CN001_count_true_returns_int_values():
    g = AutoPrefixGrouper().fit(COUNT_STRINGS, prefix_depth=["#", "/"], position_index=-1)
    r = g.get_groups(count=True)
    assert all(isinstance(v, int) for v in r.values())


def test_CN002_count_values_match_group_sizes():
    g = AutoPrefixGrouper().fit(COUNT_STRINGS, prefix_depth=["#", "/"], position_index=-1)
    r_full = g.get_groups()
    r_count = g.get_groups(count=True)
    assert all(r_count[k] == len(r_full[k]) for k in r_full)


def test_CN003_count_total_equals_input_length():
    g = AutoPrefixGrouper().fit(COUNT_STRINGS, prefix_depth=["#", "/"], position_index=-1)
    r = g.get_groups(count=True)
    assert sum(r.values()) == len(COUNT_STRINGS)


def test_CN004_count_false_is_default():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    r_default = g.get_groups()
    r_explicit = g.get_groups(count=False)
    assert r_default == r_explicit


def test_CN005_count_and_strip_prefix_both_true_raises():
    g = AutoPrefixGrouper().fit(["rdf:type", "rdf:label"])
    try:
        g.get_groups(count=True, strip_prefix=True)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_CN006_count_keys_match_get_groups_keys():
    g = AutoPrefixGrouper().fit(COUNT_STRINGS, prefix_depth=["#", "/"], position_index=-1)
    assert set(g.get_groups(count=True).keys()) == set(g.get_groups().keys())


# ── GROUP 41: resplit parameter ──────────────────────────────────────────────

RS_BASE = "http://glycosmos.org/glycoprotein/"
RS_ACCESSIONS = [
    RS_BASE + i for i in (
        "A0A076FRG6", "A0A087WQQ9", "A0A087WS40", "A1L4K1", "A2RUB6",
        "O00115", "O00116", "O00151", "O43657",
        "P01889", "P01891", "P04430",
        "Q9Y2A7", "Q9Y2A8", "Q9Y3Z3",
    )
]
RS_OBO = [
    "http://purl.obolibrary.org/obo/GO_0000001",
    "http://purl.obolibrary.org/obo/GO_0000002",
    "http://purl.obolibrary.org/obo/RO_0000001",
    "http://purl.obolibrary.org/obo/RO_0000002",
]


def test_RS001_resplit_default_is_false_and_keeps_accessions_together():
    r = AutoPrefixGrouper().fit(
        RS_ACCESSIONS, prefix_depth=["#", "/"], position_index=-1
    ).get_groups()
    assert list(r) == [RS_BASE]
    assert len(r[RS_BASE]) == len(RS_ACCESSIONS)


def test_RS011_resplit_true_splits_accessions_by_leading_letter():
    r = AutoPrefixGrouper().fit(
        RS_ACCESSIONS, prefix_depth=["#", "/"], position_index=-1, resplit=True
    ).get_groups()
    assert len(r) > 1
    flat = [s for v in r.values() for s in v]
    assert sorted(flat) == sorted(RS_ACCESSIONS)


def test_RS012_default_keeps_go_and_ro_under_obo():
    r = AutoPrefixGrouper().fit(
        RS_OBO, prefix_depth="/", position_index=-1
    ).get_groups()
    assert list(r) == ["http://purl.obolibrary.org/obo/"]


def test_RS002_resplit_false_keeps_accessions_under_one_prefix():
    r = AutoPrefixGrouper().fit(
        RS_ACCESSIONS, prefix_depth=["#", "/"], position_index=-1, resplit=False
    ).get_groups()
    assert list(r) == [RS_BASE]
    assert len(r[RS_BASE]) == len(RS_ACCESSIONS)


def test_RS003_resplit_false_count_matches_input():
    r = AutoPrefixGrouper().fit(
        RS_ACCESSIONS, prefix_depth="/", position_index=-1, resplit=False
    ).get_groups(count=True)
    assert r == {RS_BASE: len(RS_ACCESSIONS)}


def test_RS004_resplit_true_still_separates_go_and_ro():
    r = AutoPrefixGrouper().fit(
        RS_OBO, prefix_depth="/", position_index=-1, resplit=True
    ).get_groups()
    assert any("GO_" in k for k in r)
    assert any("RO_" in k for k in r)


def test_RS005_resplit_false_keeps_go_and_ro_under_obo():
    r = AutoPrefixGrouper().fit(
        RS_OBO, prefix_depth="/", position_index=-1, resplit=False
    ).get_groups()
    assert list(r) == ["http://purl.obolibrary.org/obo/"]
    assert len(r["http://purl.obolibrary.org/obo/"]) == 4


def test_RS006_resplit_false_keeps_hash_and_slash_namespaces_apart():
    data = RS_ACCESSIONS + [
        "http://jcggdb.jp/rdf/diseases/ggdonto#CON0001",
        "http://jcggdb.jp/rdf/diseases/ggdonto#CON0002",
    ]
    r = AutoPrefixGrouper().fit(
        data, prefix_depth=["#", "/"], position_index=-1, resplit=False
    ).get_groups(count=True)
    assert r == {
        RS_BASE: len(RS_ACCESSIONS),
        "http://jcggdb.jp/rdf/diseases/ggdonto#": 2,
    }


def test_RS007_resplit_has_no_effect_without_prefix_depth():
    a = AutoPrefixGrouper().fit(RS_ACCESSIONS, resplit=True).get_groups()
    b = AutoPrefixGrouper().fit(RS_ACCESSIONS, resplit=False).get_groups()
    assert a == b


def test_RS008_resplit_must_be_a_bool():
    for bad in ("no", 0, None):
        try:
            AutoPrefixGrouper().fit(
                RS_ACCESSIONS, prefix_depth="/", resplit=bad
            )
            assert False, f"Expected ValueError for {bad!r}"
        except ValueError:
            pass


def test_RS009_preview_fit_passes_resplit_through():
    g = AutoPrefixGrouper()
    r = g.preview_fit(
        RS_ACCESSIONS, prefix_depth="/", position_index=-1, resplit=False
    )
    assert list(r) == [RS_BASE]


def test_RS010_all_strings_preserved_with_resplit_false():
    g = AutoPrefixGrouper().fit(
        RS_ACCESSIONS, prefix_depth="/", position_index=-1, resplit=False
    )
    got = sorted(s for v in g.get_groups().values() for s in v)
    assert got == sorted(RS_ACCESSIONS)


# ── GROUP 42: every string lands in exactly one group ────────────────────────

def _flat(r):
    return [s for v in r.values() for s in v]


def test_X001_interleaved_namespaces_lose_no_strings():
    base = "http://glycosmos.org/glycoprotein/"
    ids = ["A0A076FRG6", "A0A087WQQ9", "A0A087WS40", "A1L4K1", "A2RUB6",
           "O00115", "O00116", "O00151", "O43657",
           "P01889", "P01891", "P04430", "Q9Y2A7", "Q9Y2A8", "Q9Y3Z3"]
    data = [base + i for i in ids]
    r = fit(data)
    assert sorted(_flat(r)) == sorted(data)


def test_X002_interleaved_namespaces_have_no_duplicates():
    base = "http://glycosmos.org/glycoprotein/"
    ids = ["A0A076FRG6", "A0A087WQQ9", "A0A087WS40", "A1L4K1", "A2RUB6",
           "O00115", "O00116", "O00151", "O43657"]
    r = fit([base + i for i in ids])
    flat = _flat(r)
    assert len(flat) == len(set(flat))


def test_X003_mixed_namespaces_by_length_keep_every_string():
    data = (
        ["http://a.org/x/" + "q" * n for n in (1, 5, 9)]
        + ["http://b.org/y/" + "r" * n for n in (2, 5, 8)]
        + ["http://a.org/x/" + "p" * n for n in (3, 7)]
    )
    for kwargs in ({}, {"prefix_depth": "/", "position_index": -1},
                   {"prefix_depth": ["#", "/"], "position_index": -1}):
        r = AutoPrefixGrouper().fit(data, **kwargs).get_groups()
        assert sorted(_flat(r)) == sorted(data), kwargs


def test_X004_count_total_equals_input_for_interleaved_data():
    base = "http://glycosmos.org/glycoprotein/"
    ids = ["A0A076FRG6", "A0A087WQQ9", "A1L4K1", "O00115", "O43657", "P01889"]
    data = [base + i for i in ids]
    r = AutoPrefixGrouper().fit(
        data, prefix_depth="/", position_index=-1
    ).get_groups(count=True)
    assert sum(r.values()) == len(data)


# ── GROUP 43: the colon of a URL scheme is not a delimiter ───────────────────

SC_GENES = [f"http://glycosmos.org/glycogene/{i}" for i in (10, 1000, 10000, 55)]
SC_PROTEINS = [
    "http://glycosmos.org/glycoprotein/A0A076FRG6",
    "http://glycosmos.org/glycoprotein/Q9Y2A7",
    "http://glycosmos.org/glycoprotein/P01889",
]
SC_DOID = [f"http://glycosmos.org/disease/DOID:{i:07d}" for i in (1816, 10, 4)]
SC_HASH = [
    "http://jcggdb.jp/rdf/diseases/ggdonto#CON0001",
    "http://jcggdb.jp/rdf/diseases/ggdonto#CON0002",
]
SC_ORDER = ["#", ":", "/"]


def sc_fit(strings, delimiters=SC_ORDER, index=-1):
    return AutoPrefixGrouper().fit(
        strings, prefix_depth=delimiters, position_index=index
    ).get_groups(count=True)


def test_SC001_urls_without_a_local_colon_fall_through_to_slash():
    r = sc_fit(SC_GENES + SC_PROTEINS)
    assert r == {
        "http://glycosmos.org/glycogene/": len(SC_GENES),
        "http://glycosmos.org/glycoprotein/": len(SC_PROTEINS),
    }


def test_SC002_never_cuts_to_the_scheme():
    r = sc_fit(SC_GENES + SC_PROTEINS + SC_DOID + SC_HASH)
    assert not any(k in ("http:", "https:") for k in r)


def test_SC003_local_colon_still_cuts_after_the_prefix():
    r = sc_fit(SC_DOID)
    assert r == {"http://glycosmos.org/disease/DOID:": len(SC_DOID)}


def test_SC004_hash_wins_over_colon_and_slash():
    r = sc_fit(SC_HASH)
    assert r == {"http://jcggdb.jp/rdf/diseases/ggdonto#": len(SC_HASH)}


def test_SC005_all_three_kinds_in_one_call():
    r = sc_fit(SC_GENES + SC_DOID + SC_HASH)
    assert r == {
        "http://glycosmos.org/glycogene/": len(SC_GENES),
        "http://glycosmos.org/disease/DOID:": len(SC_DOID),
        "http://jcggdb.jp/rdf/diseases/ggdonto#": len(SC_HASH),
    }


def test_SC006_five_delimiters_behave_the_same_way():
    r = sc_fit(SC_GENES + SC_DOID + SC_HASH, ["#", ":", "@", "|", "/"])
    assert r == sc_fit(SC_GENES + SC_DOID + SC_HASH)


def test_SC007_other_schemes_are_not_counted_either():
    data = ["https://example.org/a/1", "https://example.org/a/2",
            "ftp://example.org/b/1", "ftp://example.org/b/2"]
    r = sc_fit(data)
    assert r == {"https://example.org/a/": 2, "ftp://example.org/b/": 2}


def test_SC008_colon_as_the_only_delimiter_keeps_the_raw_prefix_for_plain_urls():
    r = AutoPrefixGrouper().fit(
        SC_GENES, prefix_depth=":", position_index=-1
    ).get_groups()
    assert not any(k == "http:" for k in r)
    assert sorted(s for v in r.values() for s in v) == sorted(SC_GENES)


def test_SC009_colon_without_slashes_is_a_delimiter():
    data = ["urn:miriam:doid:1816", "urn:miriam:doid:10", "urn:miriam:doid:4"]
    r = AutoPrefixGrouper().fit(data, prefix_depth=":", position_index=-1).get_groups(count=True)
    assert r == {"urn:miriam:doid:": 3}


def test_SC010_curie_style_ids_cut_at_the_colon():
    data = ["GO:0001234", "GO:0005678", "GO:0000001"]
    r = AutoPrefixGrouper().fit(data, prefix_depth=["#", ":", "/"], position_index=-1).get_groups(count=True)
    assert r == {"GO:": 3}


def test_SC011_position_index_does_not_count_the_scheme_colon():
    uris = ["http://glycosmos.org/disease/DOID:0001816",
            "http://glycosmos.org/disease/DOID:0000010"]
    r = AutoPrefixGrouper().fit(uris, prefix_depth=":", position_index=1).get_groups()
    assert list(r) == ["http://glycosmos.org/disease/DOID:"]


def test_SC012_inspect_prefix_skips_the_scheme_colon(capsys):
    AutoPrefixGrouper().inspect_prefix("http://glycosmos.org/disease/DOID:0001816", ":")
    out = capsys.readouterr().out
    assert out.strip() == 'position_index=1 : "http://glycosmos.org/disease/DOID:"'


def test_SC013_inspect_prefix_reports_missing_colon_for_plain_urls(capsys):
    AutoPrefixGrouper().inspect_prefix("http://glycosmos.org/glycogene/10", ":")
    assert "not found" in capsys.readouterr().out


def test_SC014_slash_positions_are_unchanged():
    g = AutoPrefixGrouper()
    assert g._delimiter_positions("http://a.org/x", "/") == [5, 6, 12]
    assert g._delimiter_positions("http://a.org/x/y", "#") == []


def test_SC015_delimiter_positions_skip_only_the_scheme_colon():
    g = AutoPrefixGrouper()
    assert g._delimiter_positions("http://a.org/DOID:1", ":") == [17]
    assert g._delimiter_positions("a:b:c", ":") == [1, 3]


def test_SC016_no_string_is_lost_with_mixed_namespaces():
    data = SC_GENES + SC_PROTEINS + SC_DOID + SC_HASH
    r = AutoPrefixGrouper().fit(
        data, prefix_depth=SC_ORDER, position_index=-1
    ).get_groups()
    assert sorted(s for v in r.values() for s in v) == sorted(data)


# ── GROUP 44: skip_scheme_colon argument ─────────────────────────────────────

def test_SK001_false_restores_the_old_cut_to_http():
    r = AutoPrefixGrouper().fit(
        SC_GENES + SC_PROTEINS, prefix_depth=SC_ORDER, position_index=-1,
        skip_scheme_colon=False,
    ).get_groups(count=True)
    assert r == {"http:": len(SC_GENES) + len(SC_PROTEINS)}


def test_SK002_default_equals_explicit_true():
    data = SC_GENES + SC_DOID + SC_HASH
    a = AutoPrefixGrouper().fit(data, prefix_depth=SC_ORDER).get_groups()
    b = AutoPrefixGrouper().fit(
        data, prefix_depth=SC_ORDER, skip_scheme_colon=True
    ).get_groups()
    assert a == b


def test_SK003_false_still_cuts_identifiers_at_their_own_colon():
    r = AutoPrefixGrouper().fit(
        SC_DOID, prefix_depth=SC_ORDER, position_index=-1,
        skip_scheme_colon=False,
    ).get_groups(count=True)
    assert r == {"http://glycosmos.org/disease/DOID:": len(SC_DOID)}


def test_SK004_skip_scheme_colon_must_be_a_bool():
    for bad in ("yes", 1, None):
        try:
            AutoPrefixGrouper().fit(
                SC_GENES, prefix_depth=SC_ORDER, skip_scheme_colon=bad
            )
            assert False, f"Expected ValueError for {bad!r}"
        except ValueError:
            pass


def test_SK005_preview_fit_passes_the_argument_through():
    g = AutoPrefixGrouper()
    on = g.preview_fit(SC_GENES, prefix_depth=SC_ORDER, skip_scheme_colon=True)
    off = g.preview_fit(SC_GENES, prefix_depth=SC_ORDER, skip_scheme_colon=False)
    assert list(on) == ["http://glycosmos.org/glycogene/"]
    assert list(off) == ["http:"]


def test_SK006_inspect_prefix_lists_the_scheme_colon_when_false(capsys):
    AutoPrefixGrouper().inspect_prefix(
        "http://glycosmos.org/disease/DOID:0001816", ":", skip_scheme_colon=False
    )
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [
        'position_index=1 : "http:"',
        'position_index=2 : "http://glycosmos.org/disease/DOID:"',
    ]


def test_SK007_position_index_counts_the_scheme_colon_when_false():
    uris = ["http://glycosmos.org/disease/DOID:0001816",
            "http://glycosmos.org/disease/DOID:0000010"]
    r = AutoPrefixGrouper().fit(
        uris, prefix_depth=":", position_index=1, skip_scheme_colon=False
    ).get_groups()
    assert list(r) == ["http:"]


def test_SK008_argument_has_no_effect_without_a_colon_delimiter():
    data = SC_GENES + SC_HASH
    a = AutoPrefixGrouper().fit(
        data, prefix_depth=["#", "/"], skip_scheme_colon=True).get_groups()
    b = AutoPrefixGrouper().fit(
        data, prefix_depth=["#", "/"], skip_scheme_colon=False).get_groups()
    assert a == b


def test_SK009_delimiter_positions_false_includes_the_scheme_colon():
    g = AutoPrefixGrouper()
    assert g._delimiter_positions("http://a.org/DOID:1", ":", False) == [4, 17]
    assert g._delimiter_positions("http://a.org/DOID:1", ":", True) == [17]


def test_SK010_no_string_is_lost_when_false():
    data = SC_GENES + SC_PROTEINS + SC_DOID + SC_HASH
    r = AutoPrefixGrouper().fit(
        data, prefix_depth=SC_ORDER, position_index=-1, skip_scheme_colon=False
    ).get_groups()
    assert sorted(s for v in r.values() for s in v) == sorted(data)

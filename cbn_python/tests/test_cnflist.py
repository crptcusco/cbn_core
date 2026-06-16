import random

from cbnetwork.cnflist import CNFList


def test_simplify_clause_removes_complements_and_duplicates():
    clause = [1, 1, -2, 2, 3]
    simplified = CNFList.simplify_clause(clause)
    # -2 and 2 cancel out, duplicates removed -> should contain 1 and 3 (order not important)
    assert set(simplified) == {1, 3}


def test_remove_duplicates_normalizes_and_removes_dupes():
    l_cnf = [[1, 2], [2, 1], [-3], [-3, -3]]
    unique = CNFList.remove_duplicates(l_cnf)
    # Expect two unique clauses: [1,2] and [-3]
    normalized = [tuple(sorted(c)) for c in unique]
    assert (1, 2) in normalized
    assert (-3,) in normalized


def test_generate_cnf_includes_external_signal_and_valid_structure():
    random.seed(0)
    l_inter_vars = [1, 2, 3, 4]
    input_sig = 99
    cnf = CNFList.generate_cnf(l_inter_vars, input_sig, max_clauses=2, max_literals=3)
    # Should be a list of non-empty clauses (lists of ints)
    assert isinstance(cnf, list)
    assert all(isinstance(clause, list) and clause for clause in cnf)
    # The first appended clause corresponds to the external signal (single literal)
    # Check that some clause is exactly [input_sig] or [-input_sig]
    assert any(len(c) == 1 and abs(c[0]) == input_sig for c in cnf)

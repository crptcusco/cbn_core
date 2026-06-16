import pytest

from cbnetwork.directededge import DirectedEdge


def test_process_true_table_and_basic_and():
    # A simple AND between two output variables 1 and 2
    de = DirectedEdge(0, 0, 0, 0, [1, 2], " 1 ∧ 2 ")
    tt = de.true_table
    # keys are ordered according to l_output_variables -> [1,2]
    assert tt["11"] == "1"
    assert tt["10"] == "0"
    assert tt["01"] == "0"
    assert tt["00"] == "0"


def test_process_true_table_unary_and_implication():
    # Test unary negation and implication
    de_not = DirectedEdge(0, 0, 0, 0, [3], " ~ 3 ")
    tt_not = de_not.true_table
    assert tt_not["1"] == "0"
    assert tt_not["0"] == "1"

    # Implication: 1 -> 2 is false only when 1 is true and 2 is false
    de_imp = DirectedEdge(0, 0, 0, 0, [1, 2], " 1 → 2 ")
    tt_imp = de_imp.true_table
    assert tt_imp["10"] == "0"
    assert tt_imp["11"] == "1"
    assert tt_imp["01"] == "1"
    assert tt_imp["00"] == "1"

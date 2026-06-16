import pytest

from cbnetwork.cbnetwork import CBN


def test_evaluate_pair_accepts_new_networks():
    # base_pairs cover networks 0 and 1
    base_pairs = [(1, 2)]
    # candidate pair from two new networks should be accepted
    candidate_pair = (5, 6)
    d_local_attractors = {
        1: (0, 0, 1),
        2: (1, 0, 1),
        5: (2, 0, 1),
        6: (3, 0, 1),
    }

    assert CBN.evaluate_pair(base_pairs, candidate_pair, d_local_attractors) is True


def test_cartesian_product_mod_filters_incompatible():
    base_pairs = [(1, 2)]
    candidate_pairs = [(5, 6), (1, 2)]
    d_local_attractors = {
        1: (0, 0, 1),
        2: (1, 0, 1),
        5: (2, 0, 1),
        6: (3, 0, 1),
    }

    result = CBN.cartesian_product_mod(base_pairs, candidate_pairs, d_local_attractors)
    # only the (5,6) candidate should combine successfully
    assert any(
        5 in [x for pair in r for x in (pair if isinstance(pair, tuple) else [pair])]
        for r in result
    )

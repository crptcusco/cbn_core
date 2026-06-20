import pytest
from cbnetwork.coupling import AndCoupling, OrCoupling, ThresholdCoupling


def test_or_coupling():
    strategy = OrCoupling()
    output_vars = [1, 2, 3]
    coupling_var = 10

    # Test string representation
    assert strategy.generate_coupling_function(output_vars) == " 1 ∨ 2 ∨ 3 "

    # Test CNF generation
    # C <=> (V1 | V2 | V3)
    # (-V1 | C), (-V2 | C), (-V3 | C), (V1 | V2 | V3 | -C)
    expected_cnf = [[-1, 10], [-2, 10], [-3, 10], [1, 2, 3, -10]]
    assert strategy.to_cnf(output_vars, coupling_var) == expected_cnf


def test_and_coupling():
    strategy = AndCoupling()
    output_vars = [1, 2, 3]
    coupling_var = 10

    # Test string representation
    assert strategy.generate_coupling_function(output_vars) == " 1 ∧ 2 ∧ 3 "

    # Test CNF generation
    # C <=> (V1 & V2 & V3)
    # (V1 | -C), (V2 | -C), (V3 | -C), (-V1 | -V2 | -V3 | C)
    expected_cnf = [[1, -10], [2, -10], [3, -10], [-1, -2, -3, 10]]
    assert strategy.to_cnf(output_vars, coupling_var) == expected_cnf


def test_threshold_coupling():
    strategy = ThresholdCoupling(threshold=2)
    output_vars = [1, 2, 3]
    coupling_var = 10

    # Test string representation
    assert (
        strategy.generate_coupling_function(output_vars) == " Threshold(2, {1, 2, 3}) "
    )

    # Test CNF generation: At least 2 of {1, 2, 3}
    # (sum(Vi) >= 2) => C  <=>  for all combos of 2: (-Vi | -Vj | C)
    # C => (sum(Vi) >= 2)  <=>  for all combos of 3-2+1=2: (Vi | Vj | -C)
    # combos of 2 from {1, 2, 3}: (1,2), (1,3), (2,3)
    expected_cnf = [
        [-1, -2, 10],
        [-1, -3, 10],
        [-2, -3, 10],
        [-10, 1, 2],
        [-10, 1, 3],
        [-10, 2, 3],
    ]
    assert strategy.to_cnf(output_vars, coupling_var) == expected_cnf


def test_threshold_coupling_invalid():
    with pytest.raises(ValueError):
        ThresholdCoupling(threshold=0)
    with pytest.raises(ValueError):
        ThresholdCoupling(threshold=-1)

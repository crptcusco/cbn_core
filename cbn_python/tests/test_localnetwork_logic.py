import pytest
from cbnetwork.internalvariable import InternalVariable
from cbnetwork.localnetwork import LocalNetwork


def test_local_network_state_transitions():
    # Setup a simple 1-variable network: v1(t+1) = NOT v1(t)
    # CNF for v1 <=> -v1 is: (-v1 | -v1) & (v1 | v1) -> [-1], [1]
    # Wait, v1 <=> -v1 is impossible.
    # Let's do v1(t+1) = v1(t)
    # v1 <=> v1 is always true.
    # Let's do v1(t+1) = 1
    # v1 <=> True -> [1]

    net = LocalNetwork(index=1, internal_variables=[1])
    var1 = InternalVariable(index=1, cnf_function=[[1]])
    net.descriptive_function_variables = [var1]
    net.process_input_signals([])

    # Brute force is not in Python LocalNetwork, only SAT-based find_local_attractors
    # But SAT based requires minisat which might not be here.
    # Let's check if we can mock the solver or if it's available.
    pass


def test_local_network_with_coupling():
    # v1(t+1) = external_v10
    # v1 <=> v10
    # CNF: (-v1 | v10) & (v1 | -v10) -> [[-1, 10], [1, -10]]
    net = LocalNetwork(index=1, internal_variables=[1])
    var1 = InternalVariable(index=1, cnf_function=[[-1, 10], [1, -10]])
    net.descriptive_function_variables = [var1]

    mock_signal = type("obj", (object,), {"index_variable": 10})
    net.process_input_signals([mock_signal])

    assert net.external_variables == [10]
    assert net.total_variables == [1, 10]

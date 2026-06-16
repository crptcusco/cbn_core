import pytest
from unittest.mock import MagicMock
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.internalvariable import InternalVariable
from cbnetwork.localscene import LocalScene


class TestBruteForce:
    @pytest.fixture
    def simple_network(self):
        # Create a simple network with 2 internal variables
        # Var 1: NOT Var 2
        # Var 2: Var 1
        # This should oscillate: (0,0) -> (1,0) -> (1,1) -> (0,1) -> (0,0) ... wait
        # Let's trace:
        # 1 = not 2
        # 2 = 1
        # State (1,2):
        # (0,0) -> (1,0)
        # (1,0) -> (1,1)
        # (1,1) -> (0,1)
        # (0,1) -> (0,0)
        # It's a cycle of length 4.

        net = LocalNetwork(index=1, internal_variables=[1, 2])

        var1 = InternalVariable(index=1, cnf_function="not 2")
        var2 = InternalVariable(index=2, cnf_function="1")

        net.descriptive_function_variables = [var1, var2]
        return net

    def test_evaluate_boolean_function_string(self):
        # Test string evaluation
        state = {1: 1, 2: 0}
        ext = {}

        # "1 and not 2" -> 1 and not 0 -> 1 and 1 -> 1
        assert LocalNetwork.evaluate_boolean_function("1 and not 2", state, ext) == 1

        # "1 and 2" -> 1 and 0 -> 0
        assert LocalNetwork.evaluate_boolean_function("1 and 2", state, ext) == 0

        # Test with symbols
        # "1 ∧ ~2" -> 1 and not 0 -> 1
        assert LocalNetwork.evaluate_boolean_function("1 ∧ ~2", state, ext) == 1

    def test_evaluate_boolean_function_cnf(self):
        # Test CNF list evaluation
        state = {1: 1, 2: 0}
        ext = {}

        # [[1, 2]] -> 1 or 2 -> 1 or 0 -> 1
        assert LocalNetwork.evaluate_boolean_function([[1, 2]], state, ext) == 1

        # [[-1]] -> not 1 -> 0
        assert LocalNetwork.evaluate_boolean_function([[-1]], state, ext) == 0

        # [[1], [-2]] -> 1 and not 2 -> 1 and 1 -> 1
        assert LocalNetwork.evaluate_boolean_function([[1], [-2]], state, ext) == 1

    def test_find_local_attractors_brute_force_cycle(self, simple_network):
        # Test finding the cycle of length 4
        net = LocalNetwork.find_local_attractors_brute_force(simple_network)

        assert len(net.local_scenes) == 1
        scene = net.local_scenes[0]
        assert len(scene.l_attractors) == 1
        attractor = scene.l_attractors[0]

        # Check cycle length
        assert len(attractor.l_states) == 4

        # Check states in cycle (order matters for the cycle, but start point can vary)
        # We know the cycle contains (0,0), (1,0), (1,1), (0,1)
        # Let's verify the values
        values = [tuple(s.l_variable_values) for s in attractor.l_states]
        assert (0, 0) in values
        assert (1, 0) in values
        assert (1, 1) in values
        assert (0, 1) in values

    def test_find_local_attractors_brute_force_fixed_point(self):
        # Stable state: 1 = 1
        net = LocalNetwork(index=1, internal_variables=[1])
        var1 = InternalVariable(index=1, cnf_function="1")
        net.descriptive_function_variables = [var1]

        net = LocalNetwork.find_local_attractors_brute_force(net)

        # assert attractor.l_states[0].l_variable_values == [1] # (1) -> (1)
        # Since we iterate from 0, we likely found (0) first.
        # Let's check that we found both (0) and (1)

        assert len(net.local_scenes[0].l_attractors) == 2

        found_values = []
        for attr in net.local_scenes[0].l_attractors:
            found_values.append(attr.l_states[0].l_variable_values[0])

        assert 0 in found_values
        assert 1 in found_values

        # Another stable state: 1 = 1 (if start 0 -> 0)
        # Wait, 1=1 means next state is value of 1.
        # If state is 0, next is 0. If state is 1, next is 1.
        # So we should have 2 attractors: (0) and (1).

        assert len(net.local_scenes[0].l_attractors) == 2

    def test_find_local_attractors_brute_force_with_external(self):
        # Var 1 = Ext 10
        net = LocalNetwork(index=1, internal_variables=[1])
        net.external_variables = [10]
        var1 = InternalVariable(index=1, cnf_function="10")
        net.descriptive_function_variables = [var1]

        # Scene 1: Ext 10 = 0 -> Attractor (0)
        # Scene 2: Ext 10 = 1 -> Attractor (1)
        scenes = [["0"], ["1"]]

        net = LocalNetwork.find_local_attractors_brute_force(net, local_scenes=scenes)

        assert len(net.local_scenes) == 2

        # Scene 0 (Ext=0)
        attr0 = net.local_scenes[0].l_attractors[0]
        assert attr0.l_states[0].l_variable_values == [0]

        # Scene 1 (Ext=1)
        attr1 = net.local_scenes[1].l_attractors[0]
        assert attr1.l_states[0].l_variable_values == [1]

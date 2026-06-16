import pytest
from unittest.mock import MagicMock, patch
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.internalvariable import InternalVariable


class TestLocalNetwork:
    @pytest.fixture
    def local_network(self):
        # Create a simple LocalNetwork for testing
        internal_variables = [1, 2, 3]
        return LocalNetwork(index=1, internal_variables=internal_variables)

    def test_initialization(self, local_network):
        assert local_network.index == 1
        assert local_network.internal_variables == [1, 2, 3]
        assert local_network.external_variables == []
        assert local_network.total_variables == []
        assert local_network.total_variables_count == 0
        assert local_network.cnf_variables_map == {}

    def test_process_input_signals(self, local_network):
        # Mock input signals
        mock_edge = MagicMock()
        mock_edge.index_variable = 10
        input_signals = [mock_edge]

        local_network.process_input_signals(input_signals)

        assert local_network.input_signals == input_signals
        assert local_network.external_variables == [10]
        assert local_network.total_variables == [1, 2, 3, 10]
        assert local_network.total_variables_count == 4
        # Check cnf_variables_map population
        # cnf_variables_map is populated in gen_boolean_formulation, not here.
        # assert local_network.cnf_variables_map[1] == 1
        # cnf_variables_map is not populated here
        assert local_network.cnf_variables_map == {}

    def test_update_internal_variable(self, local_network):
        # Mock an InternalVariable
        mock_var = MagicMock(spec=InternalVariable)
        mock_var.index = 1

        # Add it to descriptive_function_variables
        local_network.descriptive_function_variables = [mock_var]

        # Create a new variable to update with
        new_var = MagicMock(spec=InternalVariable)
        new_var.index = 1
        new_var.cnf_function = "new_function"

        updated = local_network.update_internal_variable(new_var)

        assert updated is True
        assert local_network.descriptive_function_variables[0] == new_var

    def test_update_internal_variable_not_found(self, local_network):
        mock_var = MagicMock(spec=InternalVariable)
        mock_var.index = 1
        local_network.descriptive_function_variables = [mock_var]

        new_var = MagicMock(spec=InternalVariable)
        new_var.index = 99  # Not in the list

        updated = local_network.update_internal_variable(new_var)

        assert updated is False

    def test_get_internal_variable(self, local_network):
        mock_var = MagicMock(spec=InternalVariable)
        mock_var.index = 2
        local_network.descriptive_function_variables = [mock_var]

        found_var = local_network.get_internal_variable(2)
        assert found_var == mock_var

        not_found_var = local_network.get_internal_variable(99)
        assert not_found_var is None

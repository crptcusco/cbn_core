import pytest
from unittest.mock import MagicMock, patch
from cbnetwork.cbnetwork import CBN
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.directededge import DirectedEdge


class TestCBN:
    @pytest.fixture
    def cbn_setup(self):
        # Create mock LocalNetworks
        net1 = MagicMock(spec=LocalNetwork)
        net1.index = 1
        net1.output_signals = []
        net1.attractor_count = 5

        net2 = MagicMock(spec=LocalNetwork)
        net2.index = 2
        net2.output_signals = []
        net2.attractor_count = 5

        # Create mock DirectedEdges
        edge1 = MagicMock(spec=DirectedEdge)
        edge1.index = 1
        edge1.input_local_network = 2
        edge1.output_local_network = 1
        edge1.index_variable = 10
        edge1.d_out_value_to_attractor = {0: [], 1: []}
        edge1.d_comp_pairs_attractors_by_value = {0: [], 1: []}

        l_local_networks = [net1, net2]
        l_directed_edges = [edge1]

        return l_local_networks, l_directed_edges

    def test_initialization(self, cbn_setup):
        l_local_networks, l_directed_edges = cbn_setup
        cbn = CBN(l_local_networks, l_directed_edges)

        assert cbn.l_local_networks == l_local_networks
        assert cbn.l_directed_edges == l_directed_edges
        assert cbn.d_local_attractors == {}
        assert cbn.l_global_scenes == []
        assert cbn.d_global_scenes_count == {}
        assert cbn.o_global_topology is None

        # Check if output signals were updated
        # The __init__ calls self.update_output_signals()
        # which appends edge to output_signals of the output_local_network
        # edge1 output is 1 (net1)
        assert len(l_local_networks[0].output_signals) == 1
        assert l_local_networks[0].output_signals[0] == l_directed_edges[0]

    def test_get_network_by_index(self, cbn_setup):
        l_local_networks, l_directed_edges = cbn_setup
        cbn = CBN(l_local_networks, l_directed_edges)

        net = cbn.get_network_by_index(1)
        assert net == l_local_networks[0]

        net_none = cbn.get_network_by_index(99)
        assert net_none is None

    def test_get_output_edges_by_network_index(self, cbn_setup):
        l_local_networks, l_directed_edges = cbn_setup
        cbn = CBN(l_local_networks, l_directed_edges)

        edges = cbn.get_output_edges_by_network_index(1)
        assert len(edges) == 1
        assert edges[0] == l_directed_edges[0]

        edges_empty = cbn.get_output_edges_by_network_index(2)
        assert len(edges_empty) == 0

    def test_find_compatible_pairs_parallel_with_weights(self, cbn_setup):
        # This test is complex because it involves multiprocessing.
        # We will try to mock multiprocessing.Pool to avoid actual parallel execution
        # and just verify the logic flow if possible, or test the helper methods.

        l_local_networks, l_directed_edges = cbn_setup
        cbn = CBN(l_local_networks, l_directed_edges)

        # Mock process_kind_signal
        cbn.process_kind_signal = MagicMock()

        # Mock multiprocessing.Pool imported in cbnetwork.cbnetwork
        # (the module imports `Pool` directly, so patch that name)
        with patch("cbnetwork.cbnetwork.Pool") as mock_pool:
            # Setup mock pool return
            mock_pool_instance = mock_pool.return_value
            mock_pool_instance.__enter__.return_value = mock_pool_instance

            # Mock map result
            # Expected result format: [(signal_index, d_comp_pairs, n_signal_pairs), ...]
            mock_pool_instance.map.return_value = [(1, {0: [(1, 2)], 1: [(3, 4)]}, 2)]

            cbn.find_compatible_pairs_parallel_with_weights(num_cpus=1)

            # Verify process_kind_signal was called
            assert cbn.process_kind_signal.call_count == 2

            # Verify output signal was updated
            edge = l_directed_edges[0]
            # d_comp_pairs_attractors_by_value should be updated with unique pairs
            # The mock result has {0: [(1, 2)], 1: [(3, 4)]}
            # The method converts pairs to lists of tuples/lists?
            # Let's check the implementation logic.
            # It converts pairs to tuples for set uniqueness then back to list.

            assert edge.d_comp_pairs_attractors_by_value[0] == [(1, 2)]
            assert edge.d_comp_pairs_attractors_by_value[1] == [(3, 4)]

    def test_find_local_attractors_brute_force_parallel(self, cbn_setup):
        l_local_networks, l_directed_edges = cbn_setup
        cbn = CBN(l_local_networks, l_directed_edges)

        # Mock multiprocessing.Pool imported in cbnetwork.cbnetwork
        with patch("cbnetwork.cbnetwork.multiprocessing.Pool") as mock_pool:
            # Setup mock pool return
            mock_pool_instance = mock_pool.return_value
            mock_pool_instance.__enter__.return_value = mock_pool_instance

            # Mock map result - return the networks (mocked)
            # The method expects updated networks
            mock_pool_instance.map.return_value = l_local_networks

            # Mock helper methods called after map
            cbn._assign_global_indices_to_attractors = MagicMock()
            cbn.generate_attractor_dictionary = MagicMock()

            cbn.find_local_attractors_brute_force_parallel(num_cpus=1)

            # Verify map was called with correct function
            # We can't easily check the function reference if it's a static method on class vs instance
            # But we can check it was called.
            assert mock_pool_instance.map.called
            args, _ = mock_pool_instance.map.call_args
            assert args[1] == l_local_networks

            # Verify post-processing methods called
            assert cbn._assign_global_indices_to_attractors.called
            assert cbn.generate_attractor_dictionary.called

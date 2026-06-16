import pytest
from cbnetwork.cbnetwork import CBN
from cbnetwork.localtemplates import LocalNetworkTemplate
from cbnetwork.coupling import OrCoupling

def test_generate_cbn_from_template_invalid_indices():
    """
    Tests that generate_cbn_from_template raises IndexError for invalid network indices.
    """
    o_template = LocalNetworkTemplate(
        n_vars_network=2,
        n_input_variables=1,
        n_output_variables=1,
    )

    # Invalid edge: (99, 1) where 99 is not a valid network index
    invalid_edges = [(99, 1)]

    with pytest.raises(IndexError, match="Invalid output_local_network index 99"):
        CBN.generate_cbn_from_template(
            v_topology=1,
            n_local_networks=3,
            n_vars_network=2,
            o_template=o_template,
            l_global_edges=invalid_edges,
            coupling_strategy=OrCoupling(),
        )

    # Test with an invalid input_local_network index
    invalid_edges_input = [(1, 101)]
    with pytest.raises(IndexError, match="Invalid input_local_network index 101"):
        CBN.generate_cbn_from_template(
            v_topology=1,
            n_local_networks=3,
            n_vars_network=2,
            o_template=o_template,
            l_global_edges=invalid_edges_input,
            coupling_strategy=OrCoupling(),
        )

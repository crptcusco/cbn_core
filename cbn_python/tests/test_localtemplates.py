import random

from cbnetwork.localtemplates import LocalNetworkTemplate


class DummyLocalNetwork:
    def __init__(self, index, n_vars):
        self.index = index
        self.internal_variables = [f"v{index}_{i}" for i in range(1, n_vars + 1)]


def test_generate_local_dynamic_structure():
    random.seed(1)
    n_vars = 4
    n_input = 1
    n_output = 2
    template = LocalNetworkTemplate(
        n_vars_network=n_vars,
        n_input_variables=n_input,
        n_output_variables=n_output,
        n_max_of_clauses=2,
        n_max_of_literals=2,
    )
    expected_keys = list(range(n_vars + 1, 2 * n_vars + 1))
    assert set(template.d_variable_cnf_function.keys()) == set(expected_keys)
    assert all(isinstance(v, list) for v in template.d_variable_cnf_function.values())
    assert len(template.l_output_var_indexes) == n_output
    assert all(1 <= pos <= n_vars for pos in template.l_output_var_indexes)


def test_get_output_variables_from_template():
    random.seed(2)
    n_vars = 5
    n_input = 1
    n_output = 3
    template = LocalNetworkTemplate(
        n_vars_network=n_vars,
        n_input_variables=n_input,
        n_output_variables=n_output,
        n_max_of_clauses=2,
        n_max_of_literals=2,
    )
    target_index = 999
    dummy = DummyLocalNetwork(target_index, n_vars)
    result = template.get_output_variables_from_template(target_index, [dummy])
    expected = [
        dummy.internal_variables[pos - 1] for pos in template.l_output_var_indexes
    ]
    assert result == expected

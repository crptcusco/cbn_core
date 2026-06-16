# external imports
import logging
import random

# local imports
from .cnflist import CNFList
from .utils.logging_config import setup_logging

setup_logging()


class LocalNetworkTemplate:
    def __init__(
        self,
        n_vars_network,
        n_input_variables,
        n_output_variables,
        n_max_of_clauses=None,
        n_max_of_literals=None,
        v_topology=1,
    ):
        """
        Initialize a LocalNetworkTemplate object.

        Args:
            v_topology: Topology of the network.
            n_vars_network (int): Number of variables in the network.
            n_input_variables (int): Number of input variables.
            n_output_variables (int): Number of output variables.
            n_max_of_clauses (int, optional): Maximum number of clauses for CNF functions. Defaults to None.
            n_max_of_literals (int, optional): Maximum number of literals for CNF functions. Defaults to None.
        """
        # Fixed Parameters
        self.v_topology = v_topology
        self.n_vars_network = n_vars_network
        self.n_input_variables = n_input_variables
        self.n_output_variables = n_output_variables
        # Provide default values if None is passed
        self.n_max_of_clauses = n_max_of_clauses if n_max_of_clauses is not None else 2
        self.n_max_of_literals = n_max_of_literals if n_max_of_literals is not None else 3

        # Calculated Parameters
        self.l_output_var_indexes = []
        self.d_variable_cnf_function = {}
        self.generate_local_dynamic()

    def generate_local_dynamic(self):
        """
        Generate CNF functions and output variable indexes dynamically.
        """
        # Internal variables indices
        l_internal_var_indexes = list(
            range(self.n_vars_network + 1, (self.n_vars_network * 2) + 1)
        )

        # Indices for input coupling signals, now supports multiple
        l_input_coupling_signal_indexes = list(
            range(self.n_vars_network * 2 + 1, self.n_vars_network * 2 + 1 + self.n_input_variables)
        )


        # Generate CNF function for each internal variable
        l_input_variables = random.sample(
            l_internal_var_indexes, self.n_input_variables
        )

        for i_variable in l_internal_var_indexes:
            input_coup_sig_index = None
            if i_variable in l_input_variables:
                input_coup_sig_index = random.choice(l_input_coupling_signal_indexes)

            # Generate CNF function for the variable
            self.d_variable_cnf_function[i_variable] = CNFList.generate_cnf(
                l_inter_vars=l_internal_var_indexes,
                input_coup_sig_index=input_coup_sig_index,
                max_clauses=self.n_max_of_clauses,
                max_literals=self.n_max_of_literals,
            )

        # Generate output variable indexes
        self.l_output_var_indexes = random.sample(
            range(1, self.n_vars_network + 1), self.n_output_variables
        )

    def show(self):
        """
        Display information about the LocalNetworkTemplate.
        """
        logger = logging.getLogger(__name__)
        logger.info("Local Network Template")
        logger.info("%s", "-" * 50)
        logger.info("Local dynamic:")
        for key, value in self.d_variable_cnf_function.items():
            logger.info("%s : %s", key, value)
        logger.info(
            "Output variables for coupling signal: %s", self.l_output_var_indexes
        )

    def get_output_variables_from_template(self, i_local_network, l_local_networks):
        """
        Retrieve output variables from the template based on the local network index.

        Args:
            i_local_network (int): Index of the local network.
            l_local_networks (list): List of local network objects.

        Returns:
            list: List of output variables for the specified local network.
        """
        l_variables = []
        for o_local_network in l_local_networks:
            if o_local_network.index == i_local_network:
                for position in self.l_output_var_indexes:
                    l_variables.append(o_local_network.internal_variables[position - 1])

        return l_variables


class PathCircleTemplate(LocalNetworkTemplate):
    @staticmethod
    def generate_path_circle_template(n_var_network, n_input_variables=2, n_output_variables=2, n_max_of_clauses=2, n_max_of_literals=3):
        return PathCircleTemplate(
            n_vars_network=n_var_network,
            n_input_variables=n_input_variables,
            n_output_variables=n_output_variables,
            n_max_of_clauses=n_max_of_clauses,
            n_max_of_literals=n_max_of_literals
        )

    def generate_cbn_from_template(self, v_topology, n_local_networks, coupling_strategy=None):
        # Local import to avoid circular dependency
        from .cbnetwork import CBN
        from .coupling import OrCoupling
        from .globaltopology import GlobalTopology

        if coupling_strategy is None:
            coupling_strategy = OrCoupling()

        # Generate topology to get edges
        o_global_topology = GlobalTopology.generate_sample_topology(
             v_topology=v_topology, n_nodes=n_local_networks
        )

        return CBN.generate_cbn_from_template(
            v_topology=v_topology,
            n_local_networks=n_local_networks,
            n_vars_network=self.n_vars_network,
            o_template=self,
            l_global_edges=o_global_topology.l_edges,
            coupling_strategy=coupling_strategy,
        )

# External imports
import itertools  # Provides functions for efficient looping and combination generation
import logging
import multiprocessing  # Library for parallel execution using multiple processes
import numpy as np
import os
import random  # Library for generating random numbers and shuffling data
from itertools import product
from math import ceil
from multiprocessing import Pool
from typing import (  # Type hints for better code readability and type safety
    Any,
    Dict,
    List,
    Optional,
)

from dask import (  # Library for parallel computing using task scheduling with Dask
    compute,
    delayed,
)

from .cbnetwork_utils import _convert_to_tuple as _convert_to_tuple
from .cbnetwork_utils import (
    cartesian_product_mod as _cartesian_product_mod,
    evaluate_pair as _evaluate_pair,
    flatten as _flatten,
    process_single_base_pair as _process_single_base_pair,
)
from .coupling import CouplingStrategy, OrCoupling
from .directededge import DirectedEdge

# internal imports
from .globalscene import GlobalScene
from .globaltopology import GlobalTopology
from .internalvariable import InternalVariable
from .localnetwork import LocalNetwork
from .localscene import LocalAttractor
from .localtemplates import LocalNetworkTemplate
from .utils.customtext import CustomText
from .utils.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


class CBN:
    """
    Represents a Complex Boolean Network (CBN).

    A CBN consists of multiple interconnected local Boolean networks,
    where each network can have its own set of attractors and dynamic behavior.

    Attributes:
        l_local_networks (list[LocalNetwork]):
            A list of local Boolean networks within the CBN.
        l_directed_edges (list[DirectedEdge]):
            A list of directed edges representing the interactions between local networks.
        d_local_attractors (dict):
            A dictionary mapping local networks to their respective attractors.
        d_attractor_pair (dict):
            A dictionary storing compatible attractor pairs for network transitions.
        d_attractor_fields (dict):
            A dictionary representing attractor fields, which define stable attractor configurations.
        l_global_scenes (list[GlobalScene]):
            A list of global scenes, representing different global configurations of the CBN.
        d_global_scenes_count (dict):
            A dictionary keeping track of the number of occurrences of each global scene.
        o_global_topology (GlobalTopology or None):
            An object representing the global topology of the network, initially set to None.
    """

    def __init__(self, l_local_networks: list, l_directed_edges: list):
        """
        Initializes a Complex Boolean Network with a set of local networks and directed edges.

        Args:
            l_local_networks (list[LocalNetwork]):
                The list of local networks that form the CBN.
            l_directed_edges (list[DirectedEdge]):
                The list of directed edges defining connections between local networks.
        """
        # Stores the provided local networks and edges
        self.l_local_networks = l_local_networks
        self.l_directed_edges = l_directed_edges

        # Data structures for attractor and field calculations
        self.d_local_attractors: dict = {}  # Stores attractors for each local network
        self.d_attractor_pair: dict = {}  # Stores compatible attractor pairs
        self.d_attractor_fields: dict = {}  # Stores attractor field mappings
        self.l_global_scenes: list = []  # Stores global network states
        self.d_global_scenes_count: dict = {}  # Tracks frequency of global scenes

        # Placeholder for the global topology (to be initialized later)
        self.o_global_topology = None

        # Update output signals for local networks
        self.process_output_signals()

    # PRINCIPAL FUNCTIONS
    def process_output_signals(self) -> None:
        """
        Update output signals for every local network based on directed edges.

        This method iterates over all local networks and directed edges,
        and appends each directed edge to the output signals of the local
        network if the local network's index matches the destination node
        of the directed edge.
        """
        # Create a dictionary for quick lookup of output signals
        local_network_dict = {
            network.index: network for network in self.l_local_networks
        }

        # Update output signals for each local network
        for edge in self.l_directed_edges:
            # The network that outputs the signal is edge.output_local_network
            source_network_index = edge.output_local_network
            if source_network_index in local_network_dict:
                o_local_network = local_network_dict[source_network_index]
                o_local_network.output_signals.append(edge)

    def update_network_by_index(self, o_local_network_update) -> bool:
        """
        Update a local network in the list by its index.

        Args:
            o_local_network_update (LocalNetwork): The local network object with updated information.

        Returns:
            bool: True if the network was found and updated, False otherwise.
        """
        # Iterate over the list of local networks
        for i, o_local_network in enumerate(self.l_local_networks):
            if o_local_network.index == o_local_network_update.index:
                # Update the local network in the list
                self.l_local_networks[i] = o_local_network_update
                # print(f"Local Network with index {o_local_network_update.index} updated")
                return True

        # If no network was found, print an error message
        # print(f"ERROR: Local Network with index {o_local_network_update.index} not found")
        return False

    @staticmethod
    def _generate_local_scenes(o_local_network: LocalNetwork) -> Optional[List[str]]:
        """
        Generate local scenes for the given local network based on external variables.

        Args:
            o_local_network (LocalNetwork): The local network object.

        Returns:
            Optional[List[str]]: A list of local scenes or None if there are no external variables.
        """
        external_vars_count = len(o_local_network.external_variables)
        if external_vars_count > 0:
            # Generate binary combinations for the external variables
            return [
                "".join(scene) for scene in product("01", repeat=external_vars_count)
            ]
        return None

    @staticmethod
    def process_local_network_mp(o_local_network):
        """
        Processes a local network to find its attractors.
        If an error occurs, an error message is printed, and the network is returned unchanged.

        Args:
            o_local_network: The local network object to be processed.

        Returns:
            The updated local network with its attractors found, or the original network if an error occurs.
        """
        try:
            # Generate local scenes based on external variables
            l_local_scenes = CBN._generate_local_scenes(o_local_network)
            # Find local attractors using the generated scenes
            o_local_network = LocalNetwork.find_local_attractors(
                o_local_network, l_local_scenes
            )
            return o_local_network
        except Exception as e:
            print(f"Error processing network {o_local_network.index}: {e}")
            return o_local_network

    @staticmethod
    def process_local_network_brute_force_mp(o_local_network):
        """
        Processes a local network to find its attractors using the brute-force routine.

        This mirrors `process_local_network_mp` but calls
        `LocalNetwork.find_local_attractors_brute_force` instead.
        """
        try:
            l_local_scenes = CBN._generate_local_scenes(o_local_network)
            o_local_network = LocalNetwork.find_local_attractors_brute_force(
                o_local_network, l_local_scenes
            )
            return o_local_network
        except Exception as e:
            print(
                f"Error processing (brute force) network {o_local_network.index}: {e}"
            )
            return o_local_network

    @staticmethod
    def process_output_signal_mp(args):
        """
        Processes an output signal to compute compatible attractor pairs.

        Args:
            args (tuple): Contains the following elements:
                - signal_index (int): Identifier of the signal.
                - l_attractors_input_0 (list): List of attractor indices for input value 0.
                - l_attractors_input_1 (list): List of attractor indices for input value 1.
                - index_variable (Any): The signal variable used to retrieve attractors.
                - get_attractors_func (Callable): Function to retrieve attractors,
                  typically self.get_attractors_by_input_signal_value.

        Returns:
            tuple: (signal_index, d_comp_pairs_attractors_by_value, n_pairs)
                - signal_index (int): The identifier of the processed signal.
                - d_comp_pairs_attractors_by_value (dict): Dictionary with keys {0,1},
                  where each value is a list of compatible attractor pairs.
                - n_pairs (int): The total number of attractor pairs found.
        """
        # Unpack input arguments
        (
            signal_index,
            l_attractors_input_0,
            l_attractors_input_1,
            d_var_attractors,
        ) = args

        def find_attractor_pairs(
            signal_value: int, l_attractors_input: list, l_attractors_output: list
        ):
            """
            Finds compatible attractor pairs for a given signal value.

            Args:
                signal_value (int): The value of the signal (0 or 1).
                l_attractors_input (list): List of input attractor indices.
                l_attractors_output (list): List of output attractor indices.

            Returns:
                list: A list of compatible attractor pairs as tuples.
            """
            # Generate unique pairs between input and output attractors
            unique_pairs = set(itertools.product(l_attractors_input, l_attractors_output))
            return list(unique_pairs)

        # Compute compatible pairs for both signal values (0 and 1)
        d_comp_pairs = {
            0: find_attractor_pairs(0, l_attractors_input_0, d_var_attractors[0]),
            1: find_attractor_pairs(1, l_attractors_input_1, d_var_attractors[1]),
        }

        # Count the total number of attractor pairs
        n_pairs = len(d_comp_pairs[0]) + len(d_comp_pairs[1])

        # Return the signal index, computed pairs, and the total count
        return signal_index, d_comp_pairs, n_pairs

    @staticmethod
    def evaluate_pair(
        base_pairs: list, candidate_pair: tuple, d_local_attractors
    ) -> bool:
        """
        Checks whether a candidate pair is compatible with the base pairs.

        The function recursively flattens each pair to extract individual indices and
        verifies whether the candidate pair maintains the compatibility conditions.

        Args:
            base_pairs (list): List of existing base pairs of attractors.
            candidate_pair (tuple): The new pair to evaluate.
            d_local_attractors (dict): A dictionary mapping attractor indices to their corresponding local networks.

        Returns:
            bool: True if the candidate pair is compatible, False otherwise.
        """

        def flatten(x):
            """
            Recursively flattens nested lists or tuples into a single sequence of elements.

            Args:
                x (Any): A nested list, tuple, or single element.

            Yields:
                Elements in a fully flattened form.
            """
            if isinstance(x, (list, tuple)):
                for item in x:
                    yield from flatten(item)  # Recursively flatten nested elements
            else:
                yield x  # Base case: yield individual elements

        # Flatten all base pairs to extract individual attractor indices.
        base_attractor_indices = {x for pair in base_pairs for x in flatten(pair)}

        # Extract the set of networks already visited based on base attractors.
        already_visited_networks = {
            d_local_attractors[idx][0] for idx in base_attractor_indices
        }

        double_check = 0
        # Flatten the candidate pair and check its compatibility.
        for candidate_idx in flatten(candidate_pair):
            if d_local_attractors[candidate_idx][0] in already_visited_networks:
                if candidate_idx in base_attractor_indices:
                    double_check += 1  # Candidate already exists in base pairs
            else:
                double_check += 1  # Candidate belongs to a new network

        # A valid pair must introduce exactly two new elements to the set
        return double_check == 2

    @staticmethod
    def cartesian_product_mod(
        base_pairs: list, candidate_pairs: list, d_local_attractors
    ) -> list:
        """
        Performs a modified Cartesian product between two lists of pairs, filtering out incompatible combinations.

        This function iterates through all possible combinations of `base_pairs` and `candidate_pairs`,
        checks their compatibility using `evaluate_pair`, and appends valid pairs to the result list.

        Args:
            base_pairs (list): A list of base attractor pairs.
            candidate_pairs (list): A list of new candidate attractor pairs.
            d_local_attractors (dict): A dictionary mapping attractor indices to their corresponding local networks.

        Returns:
            list: A list of new combined pairs that are considered compatible.
        """
        field_pair_list = (
            []
        )  # Stores the valid combinations of base and candidate pairs.

        for base_pair in base_pairs:
            for candidate_pair in candidate_pairs:
                # Convert base_pair to a list if it's a tuple to allow concatenation.
                if isinstance(base_pair, tuple):
                    base_pair = list(base_pair)

                # Check if the new pair is compatible before adding it.
                if CBN.evaluate_pair(base_pair, candidate_pair, d_local_attractors):
                    new_pair = base_pair + [
                        candidate_pair
                    ]  # Merge base and candidate pairs.
                    field_pair_list.append(new_pair)

        return field_pair_list

    @staticmethod
    def _convert_to_tuple(x):
        """
        Recursively converts lists into tuples to make them hashable.

        This function ensures that nested lists are transformed into immutable tuples,
        which allows them to be used as dictionary keys or stored in sets.

        Args:
            x (Any): A value that could be a list or any other data type.

        Returns:
            Any: A tuple if the input was a list, otherwise the original value.
        """
        if isinstance(x, list):
            return tuple(
                CBN._convert_to_tuple(item) for item in x
            )  # Recursively convert nested lists to tuples.
        return x  # Return unchanged if it's not a list.

    @staticmethod
    def process_single_base_pair(base_pair, candidate_pairs, d_local_attractors):
        """
        Processes a single base pair by applying `cartesian_product_mod` to generate new compatible pairs.

        This function wraps the `cartesian_product_mod` function, ensuring that the given
        base pair is processed individually by converting it into a single-element list.

        Args:
            base_pair (Any): A single base pair to be combined with candidate pairs.
            candidate_pairs (list): A list of candidate pairs to be tested for compatibility.
            d_local_attractors (dict): A dictionary mapping attractor indices to network information.

        Returns:
            list: A list of new pairs generated after applying the Cartesian product modification.
        """
        return CBN.cartesian_product_mod(
            [base_pair], candidate_pairs, d_local_attractors
        )

    def find_local_attractors_sequential(self, num_cpus: int = 2):
        """
        Finds local attractors sequentially and updates the list of local attractors in the object.

        This method calculates the local attractors for each local network, updates the coupling signals,
        assigns global indices to each attractor, and generates the attractor dictionary.
        """

        if num_cpus:
            os.environ["OMP_NUM_THREADS"] = str(num_cpus)
            os.environ["MKL_NUM_THREADS"] = str(num_cpus)

        CustomText.make_title("FIND LOCAL ATTRACTORS")

        for o_local_network in self.l_local_networks:
            # Generate the local network scenes
            local_scenes = CBN._generate_local_scenes(o_local_network)
            # Calculate the local attractors for the local network
            o_local_network = LocalNetwork.find_local_attractors(
                o_local_network, local_scenes=local_scenes
            )

        # Update the coupling signals to be analyzed
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        # Assign global indices to each attractor
        self._assign_global_indices_to_attractors()

        # Generate the attractor dictionary
        self.generate_attractor_dictionary()

        logger = logging.getLogger(__name__)
        logger.info("Number of local attractors: %d", self._count_total_attractors())
        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS")

    def find_local_attractors_brute_force_sequential(self):
        """
        Finds local attractors using brute force sequentially and updates the list of local attractors.

        This method calculates the local attractors using the brute-force engine
        for each local network, updates the coupling signals, assigns global indices,
        and generates the attractor dictionary.
        """
        CustomText.make_title("FIND LOCAL ATTRACTORS (BRUTE FORCE)")

        for o_local_network in self.l_local_networks:
            # Generate the local network scenes
            local_scenes = CBN._generate_local_scenes(o_local_network)
            # Calculate the local attractors using brute force
            o_local_network = LocalNetwork.find_local_attractors_brute_force(
                o_local_network, local_scenes=local_scenes
            )

        # Update the coupling signals
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        # Assign global indices
        self._assign_global_indices_to_attractors()

        # Generate the attractor dictionary
        self.generate_attractor_dictionary()

        logger = logging.getLogger(__name__)
        logger.info("Number of local attractors (BF): %d", self._count_total_attractors())
        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS (BRUTE FORCE)")

    def find_local_attractors_brute_force_turbo_sequential(self):
        """
        Finds local attractors using Numba-accelerated brute force sequentially.
        """
        CustomText.make_title("FIND LOCAL ATTRACTORS (TURBO BRUTE FORCE)")

        for o_local_network in self.l_local_networks:
            # Generate the local network scenes
            local_scenes = CBN._generate_local_scenes(o_local_network)
            LocalNetwork.find_local_attractors_brute_force_turbo(
                o_local_network, local_scenes=local_scenes
            )

        # Update the coupling signals
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        # Assign global indices
        self._assign_global_indices_to_attractors()

        # Generate the attractor dictionary
        self.generate_attractor_dictionary()

        logger = logging.getLogger(__name__)
        logger.info("Number of local attractors (Turbo): %d", self._count_total_attractors())
        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS (TURBO BRUTE FORCE)")

    def find_local_attractors_parallel(self, num_cpus=None):
        """Finds the attractors for each local network in parallel.

        This is the first major step in analyzing the CBN. It iterates through
        each `LocalNetwork`, considering all possible input signal combinations
        (scenes), and calculates the attractors (fixed points or cycles) for
        each scenario. This process is parallelized across multiple CPU cores.

        The results are stored internally in the `l_local_networks` and
        `d_local_attractors` attributes.

        Args:
            num_cpus: The number of CPU cores to use for parallel execution.
                If `None`, it defaults to the total number of available cores.
        """
        CustomText.make_title("FIND LOCAL ATTRACTORS PARALLEL")

        if num_cpus is None or num_cpus <= 0:
            num_cpus = multiprocessing.cpu_count()

        # Create a process pool; the number of processes can be adjusted if necessary
        with multiprocessing.Pool(processes=num_cpus) as pool:
            # map() will send each element of self.l_local_networks to the process_local_network_mp function
            updated_networks = pool.map(
                CBN.process_local_network_mp, self.l_local_networks
            )

        # Update the list of local networks with the obtained results
        self.l_local_networks = list(updated_networks)

        # Assign global indices to each attractor
        self._assign_global_indices_to_attractors()

        # Generate the attractor dictionary
        self.generate_attractor_dictionary()

        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS PARALLEL")

    def find_local_attractors_brute_force_parallel(self, num_cpus=None):
        """
        Parallelizes the process of finding local attractors using brute force.

        For each local network in self.l_local_networks:
          1. Generate its local scenes.
          2. Calculate its local attractors using brute force.

        Then, in the main process, each network is updated with its respective signal processing,
        global indices are assigned to each attractor, and the attractor dictionary is generated.
        """
        CustomText.make_title("FIND LOCAL ATTRACTORS BRUTE FORCE PARALLEL")

        if num_cpus is None or num_cpus <= 0:
            num_cpus = multiprocessing.cpu_count()

        # Create a process pool; the number of processes can be adjusted if necessary
        with multiprocessing.Pool(processes=num_cpus) as pool:
            # map() will send each element of self.l_local_networks to the process_local_network_brute_force_mp function
            updated_networks = pool.map(
                CBN.process_local_network_brute_force_mp, self.l_local_networks
            )

        # Update the list of local networks with the obtained results
        self.l_local_networks = list(updated_networks)

        # Assign global indices to each attractor
        self._assign_global_indices_to_attractors()

        # Generate the attractor dictionary
        self.generate_attractor_dictionary()

        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS BRUTE FORCE PARALLEL")

    def find_local_attractors_parallel_with_weigths(self, num_cpus=None):
        """
        Finds local attractors in parallel with multiprocessing, balancing the load
        using a 'bucket' system based on the weight of each task.
        """
        CustomText.make_title("FIND LOCAL ATTRACTORS WEIGHTED BALANCED")

        if num_cpus is None or num_cpus <= 0:
            num_cpus = multiprocessing.cpu_count()

        # Create list of tasks with weight
        tasks_with_weight = []
        for o_local_network in self.l_local_networks:
            num_vars = (
                len(o_local_network.total_variables)
                if hasattr(o_local_network, "total_variables")
                else 0
            )
            num_coupling = (
                len(o_local_network.input_signals)
                if hasattr(o_local_network, "input_signals")
                else 0
            )
            weight = num_vars * (2**num_coupling)
            tasks_with_weight.append((weight, o_local_network))

        # Sort by weight descending
        tasks_with_weight.sort(key=lambda x: x[0], reverse=True)

        # Create balanced buckets
        buckets = [{"total": 0, "tasks": []} for _ in range(num_cpus)]
        for weight, task in tasks_with_weight:
            bucket = min(buckets, key=lambda b: b["total"])
            bucket["tasks"].append(task)
            bucket["total"] += weight

        # Print initial info
        logger = logging.getLogger(__name__)
        logger.info("Number of workers: %d", num_cpus)
        logger.info("Task distribution by bucket before execution:")
        for i, bucket in enumerate(buckets):
            logger.info(
                "  Bucket %d: %d tasks, total weight: %d",
                i,
                len(bucket["tasks"]),
                bucket["total"],
            )

        # Execute in parallel with multiprocessing
        all_tasks = [task for bucket in buckets for task in bucket["tasks"]]
        with Pool(processes=num_cpus) as pool:
            results = pool.map(CBN.process_local_network_mp, all_tasks)

        # Check if any network disappeared
        if len(results) != len(self.l_local_networks):
            logger.warning(
                "Lost %d networks in the process!",
                len(self.l_local_networks) - len(results),
            )

        # Match original networks with results using indices
        ordered_results = [None] * len(self.l_local_networks)
        for original, processed in zip(all_tasks, results):
            index = self.l_local_networks.index(original)  # Find original position
            ordered_results[index] = processed

        # Check if there was any None (indicates error in assignment)
        if None in ordered_results:
            logger.warning("Some results were not reassigned correctly!")

        self.l_local_networks = ordered_results  # Assign in correct order

        # Process signals by local network
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        # Assign global indices to attractors
        self._assign_global_indices_to_attractors()
        # Generate the attractor dictionary
        self.generate_attractor_dictionary()

        # Print final bucket info
        logger.info("Final bucket information:")
        for i, bucket in enumerate(buckets):
            logger.info(
                "  Bucket %d: %d tasks, total weight: %d",
                i,
                len(bucket["tasks"]),
                bucket["total"],
            )

        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS WEIGHTED BALANCED")

    def _assign_global_indices_to_attractors(self) -> None:
        """
        Assign global indices to each attractor in all local networks.
        """
        i_attractor = 1
        for o_local_network in self.l_local_networks:
            for o_local_scene in o_local_network.local_scenes:
                for o_attractor in o_local_scene.l_attractors:
                    o_attractor.g_index = i_attractor
                    i_attractor += 1

    def generate_attractor_dictionary(self) -> None:
        """
        Generates a Dictionary of local attractors
        :return: a list of triples (a,b,c) where:
         - 'a' is the network index
         - 'b' is the scene index
         - 'c' is the local attractor index
        """
        d_local_attractors = {}
        for o_local_network in self.l_local_networks:
            for o_scene in o_local_network.local_scenes:
                for o_attractor in o_scene.l_attractors:
                    t_triple = (
                        o_local_network.index,
                        o_scene.index,
                        o_attractor.l_index,
                    )
                    d_local_attractors[o_attractor.g_index] = t_triple

        self.d_local_attractors = d_local_attractors

    def process_kind_signal(self, o_local_network: LocalNetwork) -> None:
        """
        Update the coupling signals to be analyzed for the given local network.

        Args:
            o_local_network (LocalNetwork): The local network object.
        """

        def get_true_table_index(o_state, o_output_signal):
            true_table_index = ""
            for v_output_variable in o_output_signal.l_output_variables:
                pos = o_local_network.total_variables.index(v_output_variable)
                value = o_state.l_variable_values[pos]
                true_table_index += str(value)
            return true_table_index

        def update_output_signals(l_signals_in_attractor, o_output_signal, o_attractor):
            output_value = l_signals_in_attractor[0]
            if output_value == "0":
                o_output_signal.d_out_value_to_attractor[0].append(o_attractor)
            elif output_value == "1":
                o_output_signal.d_out_value_to_attractor[1].append(o_attractor)

        l_directed_edges = CBN.find_output_edges_by_network_index(
            o_local_network.index, self.l_directed_edges
        )

        for o_output_signal in l_directed_edges:
            # Reset lists to avoid accumulation
            o_output_signal.d_out_value_to_attractor[0] = []
            o_output_signal.d_out_value_to_attractor[1] = []
            
            l_signals_for_output = []
            for o_local_scene in o_local_network.local_scenes:
                l_signals_in_local_scene = []
                for o_attractor in o_local_scene.l_attractors:
                    l_signals_in_attractor = [
                        o_output_signal.true_table[
                            get_true_table_index(o_state, o_output_signal)
                        ]
                        for o_state in o_attractor.l_states
                    ]

                    if len(set(l_signals_in_attractor)) == 1:
                        l_signals_in_local_scene.append(l_signals_in_attractor[0])
                        update_output_signals(
                            l_signals_in_attractor, o_output_signal, o_attractor
                        )

                if len(set(l_signals_in_local_scene)) == 1:
                    l_signals_for_output.append(l_signals_in_local_scene[0])
                else:
                    l_signals_for_output.extend(l_signals_in_local_scene)

            signal_set_length = len(set(l_signals_for_output))
            if signal_set_length == 1:
                o_output_signal.kind_signal = 1
                # print("INFO: the output signal is restricted")
            elif signal_set_length == 2:
                o_output_signal.kind_signal = 3
                # print("INFO: the output signal is stable")
            else:
                o_output_signal.kind_signal = 4
                # print("INFO: the scene signal is not stable. This CBN doesn't have stable Attractor Fields")

    def _count_total_attractors(self) -> int:
        """
        Count the total number of attractors across all local networks.

        Returns:
            int: The total number of attractors.
        """
        return sum(
            len(o_local_scene.l_attractors)
            for o_local_network in self.l_local_networks
            for o_local_scene in o_local_network.local_scenes
        )

    def find_compatible_pairs(self, num_cpus: int = 2) -> None:
        """
        Generate pairs of attractors using the output signal.

        Returns:
            None: Updates the dictionary of compatible attractor pairs in the object.
        """

        if num_cpus:
            os.environ["OMP_NUM_THREADS"] = str(num_cpus)
            os.environ["MKL_NUM_THREADS"] = str(num_cpus)

        CustomText.make_title("FIND COMPATIBLE ATTRACTOR PAIRS")

        # Process coupling signals for each local network
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        def find_attractor_pairs(signal_value, o_output_signal, l_attractors_input):
            """
            Find pairs of attractors based on the input signal value.

            Args:
                signal_value (int): The signal value (0 or 1).
                o_output_signal: The output signal object.
                l_attractors_input (list): List of attractor indices for the input signal.

            Returns:
                list: List of unique pairs of attractors.
            """
            l_attractors_output = [
                o_attractor.g_index
                for o_attractor in self.get_attractors_by_input_signal_value(
                    o_output_signal.index_variable, signal_value
                )
            ]

            # Use a set to avoid duplicate pairs
            unique_pairs = set(
                itertools.product(l_attractors_input, l_attractors_output)
            )

            return list(unique_pairs)

        n_pairs = 0

        for o_local_network in self.l_local_networks:
            l_output_edges = self.get_output_edges_by_network_index(
                o_local_network.index
            )

            for o_output_signal in l_output_edges:
                l_attractors_input_0 = list(
                    set(
                        attr.g_index
                        for attr in o_output_signal.d_out_value_to_attractor[0]
                    )
                )
                l_attractors_input_1 = list(
                    set(
                        attr.g_index
                        for attr in o_output_signal.d_out_value_to_attractor[1]
                    )
                )

                o_output_signal.d_comp_pairs_attractors_by_value[0] = (
                    find_attractor_pairs(0, o_output_signal, l_attractors_input_0)
                )
                o_output_signal.d_comp_pairs_attractors_by_value[1] = (
                    find_attractor_pairs(1, o_output_signal, l_attractors_input_1)
                )

                n_pairs += len(o_output_signal.d_comp_pairs_attractors_by_value[0])
                n_pairs += len(o_output_signal.d_comp_pairs_attractors_by_value[1])

        logger = logging.getLogger(__name__)
        logger.info("END FIND ATTRACTOR PAIRS (Total pairs: %d)", n_pairs)

    def find_compatible_pairs_parallel(self, num_cpus=None):
        """Finds compatible attractor pairs between connected networks in parallel.

        This is the second major step. After finding all local attractors, this
        method examines each directed edge connecting two networks. It determines
        which pairs of attractors (one from the source network, one from the
        destination) are compatible, meaning the output signal from the source's
        attractor matches the input signal expected by the destination's
        attractor.

        The results are stored within each `DirectedEdge` object.

        Args:
            num_cpus: The number of CPU cores to use for parallel execution.
                If `None`, it defaults to the total number of available cores.
        """
        CustomText.make_title("FIND COMPATIBLE ATTRACTOR PAIRS (PARALLEL)")

        # Process coupling signals for each local network
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        if num_cpus is None or num_cpus <= 0:
            num_cpus = multiprocessing.cpu_count()

        # Create a variable to attractor map to avoid pickling self or repeating searches
        # variable_index -> {0: [g_indices], 1: [g_indices]}
        var_to_attractors = {}
        
        # Pre-collect all necessary attractor mappings
        all_index_vars = set()
        for o_local_network in self.l_local_networks:
            for o_output_signal in self.get_output_edges_by_network_index(o_local_network.index):
                all_index_vars.add(o_output_signal.index_variable)
                
        for idx_var in all_index_vars:
            var_to_attractors[idx_var] = {
                0: [a.g_index for a in self.get_attractors_by_input_signal_value(idx_var, 0)],
                1: [a.g_index for a in self.get_attractors_by_input_signal_value(idx_var, 1)]
            }

        tasks = []
        signal_map = {}
        # Iterate over all local networks
        for o_local_network in self.l_local_networks:
            l_output_edges = self.get_output_edges_by_network_index(
                o_local_network.index
            )
            # Process each output signal
            for o_output_signal in l_output_edges:
                signal_index = o_output_signal.index
                signal_map[signal_index] = (
                    o_output_signal  # Save reference for later update
                )
                l_attractors_input_0 = [
                    attr.g_index for attr in o_output_signal.d_out_value_to_attractor[0]
                ]
                l_attractors_input_1 = [
                    attr.g_index for attr in o_output_signal.d_out_value_to_attractor[1]
                ]
                
                # Pass only the relevant attractor lists for this specific index_variable
                task_args = (
                    signal_index,
                    l_attractors_input_0,
                    l_attractors_input_1,
                    var_to_attractors[o_output_signal.index_variable]
                )
                tasks.append(task_args)

        logging.getLogger(__name__).info("Tasks created: %d", len(tasks))

        # Execute tasks in parallel
        with multiprocessing.Pool(processes=num_cpus) as pool:
            results = pool.map(CBN.process_output_signal_mp, tasks)

        logging.getLogger(__name__).info("Results obtained: %d", len(results))
        total_pairs = 0
        # Update output objects with obtained results
        for signal_index, d_comp_pairs, n_signal_pairs in results:
            if signal_index not in signal_map:
                logging.getLogger(__name__).error("Signal index %s not found in signal_map", signal_index)
                continue
            o_output_signal = signal_map[signal_index]
            o_output_signal.d_comp_pairs_attractors_by_value = d_comp_pairs
            total_pairs += n_signal_pairs

        CustomText.make_sub_sub_title(
            f"END FIND COMPATIBLE ATTRACTOR PAIRS (Total pairs: {total_pairs})"
        )

    def find_compatible_pairs_turbo(self) -> None:
        """
        Numba-accelerated version of Step 2: Compatible Attractor Pairs.
        """
        from cbnetwork.acceleration import evaluate_attractors_signal_kernel, find_compatible_pairs_kernel, HAS_NUMBA
        if not HAS_NUMBA:
            return self.find_compatible_pairs()

        CustomText.make_title("FIND COMPATIBLE ATTRACTOR PAIRS (TURBO)")
        
        # 1. Numerical attractor database
        # Mapping: network_index -> {
        #   states: NP array, 
        #   offsets: NP array, 
        #   lengths: NP array, 
        #   objs: list of LocalAttractor
        # }
        db = {}
        for net in self.l_local_networks:
            all_states = []
            offsets = []
            lengths = []
            objs = []
            curr_off = 0
            for scene in net.local_scenes:
                for attr in scene.l_attractors:
                    for state_obj in attr.l_states:
                        # Pack state as integer
                        state_int = 0
                        for bit_idx, val in enumerate(state_obj.l_variable_values):
                            if val:
                                state_int |= (1 << bit_idx)
                        all_states.append(state_int)
                    offsets.append(curr_off)
                    lengths.append(len(attr.l_states))
                    objs.append(attr)
                    curr_off += len(attr.l_states)
            
            if all_states:
                db[net.index] = {
                    'states': np.array(all_states, dtype=np.int64),  # 1D array of packed ints
                    'offsets': np.array(offsets, dtype=np.int64),
                    'lengths': np.array(lengths, dtype=np.int64),
                    'objs': objs
                }

        # 2. Process Kind Signal (Numerical)
        for net in self.l_local_networks:
            if net.index not in db: continue
            
            net_db = db[net.index]
            l_directed_edges = self.get_output_edges_by_network_index(net.index)
            
            for edge in l_directed_edges:
                edge.d_out_value_to_attractor[0] = []
                edge.d_out_value_to_attractor[1] = []
                
                # Prepare truth table
                n_bits = len(edge.l_output_variables)
                tt_arr = np.zeros(1 << n_bits, dtype=np.int8)
                for bit_str, val in edge.true_table.items():
                    idx = int(bit_str, 2)
                    tt_arr[idx] = val
                
                # Bit positions of output variables in the state integer
                bit_positions = np.array([
                    net.total_variables.index(v) for v in edge.l_output_variables
                ], dtype=np.int64)
                
                # Call Kernel
                attr_values = evaluate_attractors_signal_kernel(
                    net_db['states'],
                    net_db['offsets'],
                    net_db['lengths'],
                    bit_positions,
                    tt_arr
                )
                
                # Distribute results
                stable_values = []
                for i, val in enumerate(attr_values):
                    attr_obj = net_db['objs'][i]
                    if val == 0:
                        edge.d_out_value_to_attractor[0].append(attr_obj)
                        stable_values.append(0)
                    elif val == 1:
                        edge.d_out_value_to_attractor[1].append(attr_obj)
                        stable_values.append(1)
                    else:
                        stable_values.append(-2) # placeholder

                # Update kind_signal
                unique_vals = set(stable_values)
                if -2 in unique_vals:
                    edge.kind_signal = 4
                elif len(unique_vals) == 1:
                    edge.kind_signal = 1
                else:
                    edge.kind_signal = 3

        # 3. Find Compatible Pairs (Numerical)
        # Pre-collect destination attractors mapping: variable_index -> value -> [g_indices]
        dest_map = {}
        for net in self.l_local_networks:
            for scene in net.local_scenes:
                if scene.l_values is None: continue
                for i, idx_var in enumerate(scene.l_index_signals):
                    val = int(scene.l_values[i])
                    if idx_var not in dest_map: dest_map[idx_var] = {0: [], 1: []}
                    dest_map[idx_var][val].extend([a.g_index for a in scene.l_attractors])

        total_pairs = 0
        for edge in self.l_directed_edges:
            idx_var = edge.index_variable
            if idx_var not in dest_map: continue
            
            dest_info = dest_map[idx_var]
            for val in [0, 1]:
                src_indices = np.array([a.g_index for a in edge.d_out_value_to_attractor[val]], dtype=np.int32)
                dst_indices = np.array(dest_info[val], dtype=np.int32)
                
                if len(src_indices) > 0 and len(dst_indices) > 0:
                    pairs_arr = find_compatible_pairs_kernel(src_indices, dst_indices)
                    # Convert back to list of tuples for compatibility
                    edge.d_comp_pairs_attractors_by_value[val] = [tuple(p) for p in pairs_arr]
                    total_pairs += len(pairs_arr)
                else:
                    edge.d_comp_pairs_attractors_by_value[val] = []

        logging.getLogger(__name__).info("END FIND ATTRACTOR PAIRS (TURBO) (Total pairs: %d)", total_pairs)

    def find_compatible_pairs_parallel_with_weights(self, num_cpus=None):
        """
        Parallelizes the generation of compatible pairs using multiprocessing,
        assigning tasks (each corresponding to a coupling signal) to weight-balanced buckets.
        The weight of each task is calculated as:

             weight = len(l_attractors_input_0) + len(l_attractors_input_1)

        Then, all tasks are executed in parallel, and the original objects are updated.
        """
        CustomText.make_title("FIND COMPATIBLE ATTRACTOR PAIRS (PARALLEL WITH WEIGHTS)")

        # Process coupling signals for each local network
        for local_network in self.l_local_networks:
            self.process_kind_signal(local_network)

        if num_cpus is None or num_cpus <= 0:
            num_cpus = multiprocessing.cpu_count()

        tasks_with_weight = []
        signal_map = {}

        # Iterate over each local network and its output signals
        for local_network in self.l_local_networks:
            output_edges = self.get_output_edges_by_network_index(local_network.index)
            for output_signal in output_edges:

                # Get the number of attractors in the input network
                input_network = self.get_network_by_index(
                    output_signal.input_local_network
                )
                n_local_attractors = input_network.attractor_count

                signal_index = output_signal.index
                # Save the reference for later update
                signal_map[signal_index] = output_signal
                l_attractors_input_0 = [
                    attr.g_index for attr in output_signal.d_out_value_to_attractor[0]
                ]
                l_attractors_input_1 = [
                    attr.g_index for attr in output_signal.d_out_value_to_attractor[1]
                ]
                # Define the task's weight (you can adjust this formula if needed)
                weight = (
                    len(l_attractors_input_0) + len(l_attractors_input_1)
                ) * n_local_attractors
                task_args = (
                    signal_index,
                    l_attractors_input_0,
                    l_attractors_input_1,
                    output_signal.index_variable,
                    self.get_attractors_by_input_signal_value,
                )
                tasks_with_weight.append((weight, task_args))

        # Sort the tasks by weight, from highest to lowest
        tasks_with_weight.sort(key=lambda x: x[0], reverse=True)

        # Create buckets to balance the load across the CPUs
        buckets = [{"total": 0, "tasks": []} for _ in range(num_cpus)]
        for weight, task in tasks_with_weight:
            bucket = min(buckets, key=lambda b: b["total"])
            bucket["tasks"].append(task)
            bucket["total"] += weight

        # Print bucket information before execution
        logger = logging.getLogger(__name__)
        logger.info("Number of CPUs: %d", num_cpus)
        logger.info("Task distribution by bucket before execution:")
        for i, bucket in enumerate(buckets):
            logger.info(
                "  Bucket %d: %d tasks, total weight: %d",
                i,
                len(bucket["tasks"]),
                bucket["total"],
            )

        # Combine all tasks into a single list for parallel execution
        all_tasks = []
        for bucket in buckets:
            all_tasks.extend(bucket["tasks"])

        # Execute all tasks in parallel using multiprocessing
        with Pool(processes=num_cpus) as pool:
            results = pool.map(CBN.process_output_signal_mp, all_tasks)

        logging.getLogger(__name__).info("Number of tasks processed: %d", len(results))

        total_pairs = 0
        # Update output signal objects with the obtained results
        for signal_index, d_comp_pairs, n_signal_pairs in results:
            if signal_index not in signal_map:
                logging.getLogger(__name__).error(
                    "Error: Signal index %s not found in signal_map", signal_index
                )
                continue
            output_signal = signal_map[signal_index]

            # Remove duplicates from the compatible pairs dictionary.
            # d_comp_pairs is expected to be a dictionary with keys 0 and 1.
            unique_pairs_dict = {}
            new_n_signal_pairs = 0
            for key, pair_list in d_comp_pairs.items():
                unique_set = set()
                for pair in pair_list:
                    # Convert each pair to a tuple to ensure hashability
                    unique_set.add(tuple(pair))
                unique_pairs_list = list(unique_set)
                unique_pairs_dict[key] = unique_pairs_list
                new_n_signal_pairs += len(unique_pairs_list)

            output_signal.d_comp_pairs_attractors_by_value = unique_pairs_dict
            total_pairs += new_n_signal_pairs

        logging.getLogger(__name__).info(
            "END FIND COMPATIBLE ATTRACTOR PAIRS (Total unique pairs: %d)", total_pairs
        )

    def order_edges_by_compatibility(self):
        """
        Order the directed edges based on their compatibility.

        The compatibility is determined if the input or output local network of one edge
        matches with the input or output local network of any edge in the base group.
        """

        def is_compatible(l_group_base, o_group):
            """
            Check if the given edge group is compatible with any edge in the base group.

            Args:
                l_group_base (list): List of base edge groups.
                o_group: Edge group to be checked for compatibility.

            Returns:
                bool: True if compatible, False otherwise.
            """
            for aux_par in l_group_base:
                if (
                    aux_par.input_local_network == o_group.input_local_network
                    or aux_par.input_local_network == o_group.output_local_network
                ):
                    return True
                elif (
                    aux_par.output_local_network == o_group.output_local_network
                    or aux_par.output_local_network == o_group.input_local_network
                ):
                    return True
            return False

        # Initialize the base list with the first edge group
        l_base = [self.l_directed_edges[0]]
        aux_l_rest_groups = self.l_directed_edges[1:]

        # Process each remaining edge group
        for v_group in aux_l_rest_groups:
            if is_compatible(l_base, v_group):
                l_base.append(v_group)
            else:
                # If not compatible, move it to the end of the list
                aux_l_rest_groups.remove(v_group)
                aux_l_rest_groups.append(v_group)

        # Combine the base list with the rest of the groups
        self.l_directed_edges = [self.l_directed_edges[0]] + aux_l_rest_groups
        # print("Directed Edges ordered.")

    def order_edges_by_grade(self):
        """
        Orders the directed edges based on the total degree of the networks they connect.

        The total degree of an edge is the sum of the degrees of its input and output networks.
        The edges are then reordered to keep adjacent edges (sharing networks) close together.
        """

        # Step 1: Calculate the degree of each local network
        network_degrees = {net.index: 0 for net in self.l_local_networks}

        for edge in self.l_directed_edges:
            network_degrees[edge.input_local_network] += 1
            network_degrees[edge.output_local_network] += 1

        # Step 2: Calculate the "total grade" of each edge
        def calculate_edge_grade(edge):
            input_degree = network_degrees.get(edge.input_local_network, 0)
            output_degree = network_degrees.get(edge.output_local_network, 0)
            return input_degree + output_degree

        # Step 3: Sort edges by total grade in descending order
        self.l_directed_edges.sort(key=calculate_edge_grade, reverse=True)

        # Step 4: Reorder to keep adjacent edges together
        def is_adjacent(edge1, edge2):
            return (
                edge1.input_local_network == edge2.input_local_network
                or edge1.input_local_network == edge2.output_local_network
                or edge1.output_local_network == edge2.input_local_network
                or edge1.output_local_network == edge2.output_local_network
            )

        ordered_edges = [
            self.l_directed_edges.pop(0)
        ]  # Start with the highest grade edge

        while self.l_directed_edges:
            for i, edge in enumerate(self.l_directed_edges):
                if is_adjacent(ordered_edges[-1], edge):
                    ordered_edges.append(self.l_directed_edges.pop(i))
                    break
            else:
                # If no adjacent edge found, add the next available one
                ordered_edges.append(self.l_directed_edges.pop(0))

        # Step 5: Update the list of edges
        self.l_directed_edges = ordered_edges

    def disorder_edges(self):
        """
        Randomly shuffles the list of directed edges, ensuring that the first edge
        does not share vertices with the second one, and reassigns the edges in the structure.
        """
        if len(self.l_directed_edges) < 2:
            return  # Not enough edges to apply the condition

        # Randomly shuffle the edges
        random.shuffle(self.l_directed_edges)

        # Check if the first and second edges share any vertex
        def have_common_vertex(edge1, edge2):
            return edge1.input_local_network in {
                edge2.input_local_network,
                edge2.output_local_network,
            } or edge1.output_local_network in {
                edge2.input_local_network,
                edge2.output_local_network,
            }

        # If the first and second edges have a common vertex, find a new second edge
        if have_common_vertex(self.l_directed_edges[0], self.l_directed_edges[1]):
            for i in range(2, len(self.l_directed_edges)):
                if not have_common_vertex(
                    self.l_directed_edges[0], self.l_directed_edges[i]
                ):
                    # Swap the second edge with one that does not share vertices
                    self.l_directed_edges[1], self.l_directed_edges[i] = (
                        self.l_directed_edges[i],
                        self.l_directed_edges[1],
                    )
                    break

    def mount_stable_attractor_fields(self) -> None:
        """Assembles the global attractors (Attractor Fields) of the CBN.

        This is the final analysis step. It takes the compatible pairs found in
        the previous step and chains them together to build "Attractor Fields".
        An attractor field represents a stable global state of the entire
        Coupled Boolean Network, where every local network is in a stable
        attractor and all coupling signals between them are consistent.

        This implementation uses a fusion-based approach, starting with
        individual compatible pairs and iteratively merging them into larger fields
        if they share a common local attractor.

        The results are stored in the `d_attractor_fields` dictionary.
        """
        CustomText.make_title("FIND ATTRACTOR FIELDS")

        # 1. Collect all compatible pairs from all edges into a single list
        all_pairs = []
        for edge in self.l_directed_edges:
            all_pairs.extend(edge.d_comp_pairs_attractors_by_value.get(0, []))
            all_pairs.extend(edge.d_comp_pairs_attractors_by_value.get(1, []))

        if not all_pairs:
            self.d_attractor_fields = {}
            CustomText.make_sub_sub_title("END MOUNT ATTRACTOR FIELDS")
            return

        # 2. Initialize fields, where each field is initially a single pair
        fields = [set(pair) for pair in all_pairs]

        # 3. Iteratively merge fields that have a non-empty intersection
        merged = True
        while merged:
            merged = False
            i = 0
            while i < len(fields):
                j = i + 1
                while j < len(fields):
                    # If two fields share any attractor, merge them
                    if fields[i].intersection(fields[j]):
                        fields[i].update(fields[j])
                        fields.pop(j)
                        merged = True
                    else:
                        j += 1
                i += 1

        # 4. Remove duplicate fields
        unique_fields = []
        for field in fields:
            if field not in unique_fields:
                unique_fields.append(field)

        # 5. Generate the final dictionary of attractor fields
        self.d_attractor_fields = {
            i + 1: sorted(list(field)) for i, field in enumerate(unique_fields)
        }

        CustomText.make_sub_sub_title("END MOUNT ATTRACTOR FIELDS")

    def mount_stable_attractor_fields_turbo(self) -> None:
        """
        Numba-accelerated version of Step 3: Mount Stable Attractor Fields.
        Uses numerical arrays and JIT-compiled kernels for faster field assembly.
        """
        from cbnetwork.acceleration import filter_compatible_pairs_kernel, HAS_NUMBA
        if not HAS_NUMBA:
            return self.mount_stable_attractor_fields()

        CustomText.make_title("FIND ATTRACTOR FIELDS (TURBO)")
        
        # Order edges by compatibility
        self.order_edges_by_compatibility()
        
        # Build attractor-to-network mapping
        max_attr_idx = max(self.d_local_attractors.keys())
        attr_to_network = np.zeros(max_attr_idx + 1, dtype=np.int32)
        for attr_idx, attr_data in self.d_local_attractors.items():
            # d_local_attractors[idx] = (network_idx, scene_idx, attractor_obj)
            net_idx = attr_data[0]
            attr_to_network[attr_idx] = net_idx
        
        # Initialize with first edge
        first_edge = self.l_directed_edges[0]
        base_pairs_list = (
            first_edge.d_comp_pairs_attractors_by_value[0] +
            first_edge.d_comp_pairs_attractors_by_value[1]
        )
        
        if not base_pairs_list:
            self.d_attractor_fields = {}
            CustomText.make_sub_sub_title("END MOUNT ATTRACTOR FIELDS (TURBO)")
            return
        
        # Convert base pairs to numerical format
        # Each field is represented as a list of attractor indices
        current_fields = []
        for pair in base_pairs_list:
            current_fields.append(list(pair))
        
        # Process each remaining edge
        for edge_idx, o_directed_edge in enumerate(self.l_directed_edges[1:], start=1):
            candidate_pairs_list = (
                o_directed_edge.d_comp_pairs_attractors_by_value[0] +
                o_directed_edge.d_comp_pairs_attractors_by_value[1]
            )
            
            if not candidate_pairs_list or not current_fields:
                current_fields = []
                break
            
            # Prepare data for Numba kernel
            n_fields = len(current_fields)
            n_pairs = len(candidate_pairs_list)
            
            # Find max field size for padding
            max_field_size = max(len(f) for f in current_fields)
            
            # Create padded arrays
            fields_array = np.full((n_fields, max_field_size), -1, dtype=np.int32)
            field_sizes = np.zeros(n_fields, dtype=np.int32)
            field_networks = np.full((n_fields, max_field_size), -1, dtype=np.int32)
            
            for i, field in enumerate(current_fields):
                field_sizes[i] = len(field)
                for j, attr_idx in enumerate(field):
                    fields_array[i, j] = attr_idx
                    field_networks[i, j] = attr_to_network[attr_idx]
            
            # Candidate pairs array
            pairs_array = np.array(candidate_pairs_list, dtype=np.int32)
            
            # Call Numba kernel
            compatible_matrix = filter_compatible_pairs_kernel(
                fields_array,
                field_sizes,
                field_networks,
                pairs_array,
                attr_to_network
            )
            
            # Build new fields from compatibility matrix
            new_fields = []
            for i in range(n_fields):
                for j in range(n_pairs):
                    if compatible_matrix[i, j]:
                        # Combine field with pair
                        new_field = current_fields[i] + list(candidate_pairs_list[j])
                        new_fields.append(new_field)
            
            current_fields = new_fields
            
            if not current_fields:
                break
        
        # Generate final attractor fields dictionary
        self.d_attractor_fields = {}
        for i, field in enumerate(current_fields, start=1):
            # Remove duplicates and convert to list
            self.d_attractor_fields[i] = list(set(field))
        
        logging.getLogger(__name__).info(
            "END MOUNT ATTRACTOR FIELDS (TURBO) (Total fields: %d)", 
            len(self.d_attractor_fields)
        )
        CustomText.make_sub_sub_title("END MOUNT ATTRACTOR FIELDS (TURBO)")

    def mount_stable_attractor_fields_parallel(self, num_cpus=None):
        """Assemble stable attractor fields in parallel using multiprocessing.

        Process overview:
        1. Order edges by compatibility.
        2. Generate initial base pairs from the first edge.
        3. For each remaining edge, process base pairs in parallel and update the base.
        4. Build attractor fields from the final base and store them in
           ``self.d_attractor_fields``.
        """

        if num_cpus:
            os.environ["OMP_NUM_THREADS"] = str(num_cpus)
            os.environ["MKL_NUM_THREADS"] = str(num_cpus)

        CustomText.make_title("MOUNT STABLE ATTRACTOR FIELDS (PARALLEL)")

        if num_cpus is None or num_cpus <= 0:
            num_cpus = multiprocessing.cpu_count()

        # Paso 1: Ordenar las aristas por compatibilidad
        self.order_edges_by_compatibility()

        # Paso 2: Generar la base inicial de pares a partir de la primera arista
        base0 = self.l_directed_edges[0].d_comp_pairs_attractors_by_value[0]
        base1 = self.l_directed_edges[0].d_comp_pairs_attractors_by_value[1]
        l_base_pairs = set(base0 + base1)

        # Paso 3: Iterar sobre las aristas restantes para refinar la base de pares
        for o_directed_edge in self.l_directed_edges[1:]:
            l_candidate_pairs = (
                o_directed_edge.d_comp_pairs_attractors_by_value[0]
                + o_directed_edge.d_comp_pairs_attractors_by_value[1]
            )
            logger.info(
                "Procesando arista %s con %d pares base",
                o_directed_edge.index,
                len(l_base_pairs),
            )

            base_pairs_list = list(l_base_pairs)
            tasks_args = [
                (bp, l_candidate_pairs, self.d_local_attractors)
                for bp in base_pairs_list
            ]

            with Pool(processes=num_cpus) as pool:
                results = pool.starmap(CBN.process_single_base_pair, tasks_args)

            new_base_pairs = set()
            for r in results:
                for item in r:
                    if isinstance(item, list):
                        new_base_pairs.add(tuple(item))
                    else:
                        new_base_pairs.add(item)
            l_base_pairs = new_base_pairs

            logger.info("Base actualizada: %d pares", len(l_base_pairs))
            if not l_base_pairs:
                break

        # Paso 4: Generar el diccionario de campos de atractores a partir de la base final
        self.d_attractor_fields = {}
        for i, base_element in enumerate(l_base_pairs, start=1):
            field = set()
            try:
                for pair in base_element:
                    try:
                        for item in pair:
                            field.add(tuple(item) if isinstance(item, list) else item)
                    except TypeError:
                        field.add(pair)
            except TypeError:
                field.add(base_element)
            self.d_attractor_fields[i] = list(field)

        CustomText.make_sub_sub_title("END MOUNT STABLE ATTRACTOR FIELDS (PARALLEL)")

    @staticmethod
    def flatten(x):
        """
        Recursively flattens a nested list or tuple into a single sequence.
        """
        if isinstance(x, (list, tuple)):
            for item in x:
                yield from CBN.flatten(item)
        else:
            yield x

    def mount_stable_attractor_fields_parallel_chunks(self, num_cpus=None):
        """
        Assembles stable attractor fields in parallel using multiprocessing.

        The process is:
          1. Order the edges by compatibility.
          2. Generate the initial base pairs from the first edge.
          3. For each remaining edge:
               - Extract the candidate pairs for the current output signal.
               - Divide the current base into uniform chunks (based on num_cpus).
               - Process each chunk in parallel using cartesian_product_mod,
                 passing the candidate list and the d_local_attractors dictionary.
               - Merge the results (via set union) to update the base pairs.
          4. Finally, generate the attractor fields dictionary from the final base.

        Updates self.d_attractor_fields with the found fields.
        """
        CustomText.make_title("MOUNT STABLE ATTRACTOR FIELDS (PARALLEL CHUNKS)")

        if num_cpus is None or num_cpus <= 0:
            num_cpus = multiprocessing.cpu_count()

        # Step 1: Order the edges by compatibility
        self.order_edges_by_compatibility()

        # Step 2: Generate the initial base pairs from the first edge
        initial_pairs = (
            self.l_directed_edges[0].d_comp_pairs_attractors_by_value[0]
            + self.l_directed_edges[0].d_comp_pairs_attractors_by_value[1]
        )
        # Convert each element to a tuple, encapsulating if necessary
        l_base_pairs = set(
            tuple(item) if isinstance(item, (list, tuple)) else (item,)
            for item in initial_pairs
        )

        # Step 3: Iterate over the remaining edges to refine the base pairs
        for directed_edge in self.l_directed_edges[1:]:
            # Extract the candidate pairs for the current output signal
            candidate_pairs = (
                directed_edge.d_comp_pairs_attractors_by_value[0]
                + directed_edge.d_comp_pairs_attractors_by_value[1]
            )

            # Divide the current base into uniform chunks
            l_base_pairs_list = list(l_base_pairs)
            n = len(l_base_pairs_list)
            if n == 0:
                break
            chunk_size = ceil(n / num_cpus)
            chunks = [
                l_base_pairs_list[i : i + chunk_size] for i in range(0, n, chunk_size)
            ]

            logger.info(
                "Processing edge %s with %d base pairs; chunk size: %d",
                directed_edge.index,
                n,
                chunk_size,
            )
            for i, chunk in enumerate(chunks):
                logger.info("  Chunk %d: %d pairs", i, len(chunk))

            # Execute in parallel: for each chunk, call cartesian_product_mod
            with Pool(processes=num_cpus) as pool:
                args = [
                    (chunk, candidate_pairs, self.d_local_attractors)
                    for chunk in chunks
                ]
                iter_results = pool.starmap(CBN.cartesian_product_mod, args)

            # Merge the results: each result may be a list of new pairs
            new_base_pairs = set()
            for result in iter_results:
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, (list, tuple)):
                            new_base_pairs.add(tuple(item))
                        else:
                            new_base_pairs.add((item,))
                elif isinstance(result, (list, tuple)):
                    new_base_pairs.add(tuple(result))
                else:
                    new_base_pairs.add((result,))

            # Update the base pairs for the next iteration
            l_base_pairs = new_base_pairs
            logger.info("Updated base: %d pairs", len(l_base_pairs))
            if not l_base_pairs:
                break

        # Step 4: Generate the dictionary of attractor fields from the final base
        self.d_attractor_fields = {}
        for i, base_element in enumerate(l_base_pairs, start=1):
            # Flatten the base element to obtain a flat list of attractor indices
            flat_field = list(CBN.flatten(base_element))
            # Remove duplicates while preserving order
            seen = set()
            unique_flat_field = []
            for item in flat_field:
                if item not in seen:
                    seen.add(item)
                    unique_flat_field.append(item)
            self.d_attractor_fields[i] = unique_flat_field

        CustomText.make_sub_sub_title(
            f"END MOUNT STABLE ATTRACTOR FIELDS (Total:{len(l_base_pairs)})"
        )

    # DASK FUNCTIONS
    def dask_find_local_attractors(self):
        """
        Parallelizes the process of finding local attractors using Dask.

        This function divides the calculation of local attractors into parallel subtasks and then combines the results.
        """
        CustomText.make_title("FIND LOCAL ATTRACTORS")

        # Step 1: Create parallel tasks to find local attractors
        def process_local_network(o_local_network):
            """
            Processes a local network: generates local scenes, finds attractors, and processes signals.
            """
            # Generate local scenes
            local_scenes = CBN._generate_local_scenes(o_local_network)

            # Find local attractors
            updated_network = LocalNetwork.find_local_attractors(
                o_local_network, local_scenes=local_scenes
            )

            return updated_network

        # Create a list of tasks using dask.delayed
        delayed_tasks = [
            delayed(process_local_network)(o_local_network)
            for o_local_network in self.l_local_networks
        ]

        # Execute all tasks in parallel
        updated_networks = compute(*delayed_tasks)

        # Update local networks with the results
        self.l_local_networks = list(
            updated_networks
        )  # Convert tuple to list to maintain original format

        # Process coupling signals
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        # Step 2: Assign global indices to each attractor
        self._assign_global_indices_to_attractors()

        # Step 3: Generate the attractor dictionary
        self.generate_attractor_dictionary()

        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS")

    def dask_find_local_attractors_weighted_balanced(self, num_workers):
        """
        Parallelizes the process of finding local attractors using Dask,
        allocating tasks according to a weight defined as:

             weight = (number of variables) * 2^(number of coupling signals)

        Then, tasks are grouped into 'num_workers' buckets so that the total weight
        of each bucket is as balanced as possible. Finally, all tasks are scheduled
        simultaneously to run concurrently, and the CBN structure is updated.
        """
        CustomText.make_title("FIND LOCAL ATTRACTORS WEIGHTED BALANCED")

        # Function to be executed for each local network
        def process_local_network(o_local_network):
            # Generates local scenes using the static CBN method
            local_scenes = CBN._generate_local_scenes(o_local_network)
            # Finds local attractors for the network (assumes this method internally updates the object)
            updated_network = LocalNetwork.find_local_attractors(
                o_local_network, local_scenes=local_scenes
            )
            return updated_network

        # Create a list of tasks along with their weight
        tasks_with_weight = []
        for o_local_network in self.l_local_networks:
            # Assumes each local network has:
            #  - total_variables: list of variables (internal/external/total)
            #  - input_signals: list of coupling signals (or similar attribute)
            num_vars = (
                len(o_local_network.total_variables)
                if hasattr(o_local_network, "total_variables")
                else 0
            )
            num_coupling = (
                len(o_local_network.input_signals)
                if hasattr(o_local_network, "input_signals")
                else 0
            )
            weight = num_vars * (2**num_coupling)
            delayed_task = delayed(process_local_network)(o_local_network)
            tasks_with_weight.append((weight, delayed_task))

        # Sort tasks by weight in descending order
        tasks_with_weight.sort(key=lambda x: x[0], reverse=True)

        # Create buckets (groups) for each worker to balance the load
        buckets = [{"total": 0, "tasks": []} for _ in range(num_workers)]
        for weight, task in tasks_with_weight:
            # Assign the task to the bucket with the lowest accumulated weight
            bucket = min(buckets, key=lambda b: b["total"])
            bucket["tasks"].append(task)
            bucket["total"] += weight

        # For debugging, print the accumulated weights of each bucket
        for i, bucket in enumerate(buckets):
            logger.info(
                "Bucket %d total weight: %d with %d tasks",
                i,
                bucket["total"],
                len(bucket["tasks"]),
            )

        # Instead of computing each bucket sequentially, combine all tasks
        all_tasks = []
        for bucket in buckets:
            all_tasks.extend(bucket["tasks"])

        # Execute all tasks simultaneously
        results = compute(*all_tasks)

        # Update the list of local networks with the combined results
        self.l_local_networks = list(results)

        # Process coupling signals for each local network (additional step in the flow)
        for o_local_network in self.l_local_networks:
            self.process_kind_signal(o_local_network)

        # Step 2: Assign global indices to each attractor
        self._assign_global_indices_to_attractors()

        # Step 3: Generate the attractor dictionary
        self.generate_attractor_dictionary()

        CustomText.make_sub_sub_title("END FIND LOCAL ATTRACTORS WEIGHTED BALANCED")

    def dask_find_compatible_pairs(self) -> None:
        """
        Parallelizes the generation of attractor pairs using output signals.

        Uses Dask to calculate compatible pairs and ensures that the results
        are correctly integrated into the original objects.
        """
        CustomText.make_title("FIND COMPATIBLE ATTRACTOR PAIRS")

        # Helper function to find attractor pairs
        def find_attractor_pairs(
            signal_value, o_output_signal_index_variable, l_attractors_input
        ):
            """
            Finds attractor pairs based on the input signal value.

            Args:
                signal_value (int): The signal value (0 or 1).
                o_output_signal_index_variable: Variable index of the output signal object.
                l_attractors_input (list): List of attractor indices for the input signal.

            Returns:
                list: List of attractor pairs.
            """
            l_attractors_output = [
                o_attractor.g_index
                for o_attractor in self.get_attractors_by_input_signal_value(
                    o_output_signal_index_variable, signal_value
                )
            ]
            return list(itertools.product(l_attractors_input, l_attractors_output))

        # Helper function to process an output signal
        def process_output_signal(
            signal_index, l_attractors_input_0, l_attractors_input_1, index_variable
        ):
            """
            Processes an output signal and finds compatible pairs.

            Args:
                signal_index: Index of the output signal.
                l_attractors_input_0: List of attractors for value 0.
                l_attractors_input_1: List of attractors for value 1.
                index_variable: Index variable of the signal.

            Returns:
                dict: Dictionary with attractor pairs.
            """
            d_comp_pairs_attractors_by_value = {
                0: find_attractor_pairs(0, index_variable, l_attractors_input_0),
                1: find_attractor_pairs(1, index_variable, l_attractors_input_1),
            }

            # Returns the signal index and the generated dictionary
            n_pairs = len(d_comp_pairs_attractors_by_value[0]) + len(
                d_comp_pairs_attractors_by_value[1]
            )
            return signal_index, d_comp_pairs_attractors_by_value, n_pairs

        # Create a list of parallel tasks
        delayed_tasks = []
        signal_map = {}
        for o_local_network in self.l_local_networks:
            l_output_edges = self.get_output_edges_by_network_index(
                o_local_network.index
            )
            for o_output_signal in l_output_edges:
                signal_index = o_output_signal.index
                signal_map[signal_index] = (
                    o_output_signal  # Mapping to access original objects
                )
                l_attractors_input_0 = [
                    attr.g_index for attr in o_output_signal.d_out_value_to_attractor[0]
                ]
                l_attractors_input_1 = [
                    attr.g_index for attr in o_output_signal.d_out_value_to_attractor[1]
                ]
                delayed_tasks.append(
                    delayed(process_output_signal)(
                        signal_index,
                        l_attractors_input_0,
                        l_attractors_input_1,
                        o_output_signal.index_variable,
                    )
                )

        # Before computing tasks
        logger.info("Tasks created: %d", len(delayed_tasks))
        for task in delayed_tasks[:5]:  # Show only the first 5
            logger.debug("%s", task)

        # Execute tasks in parallel
        results = compute(*delayed_tasks)

        # After executing compute
        logger.info("Results obtained: %d", len(results))
        for result in results[:5]:
            logger.debug("%s", result)

        for idx, result in enumerate(
            results[:5]
        ):  # Show only the first 5 to avoid too much information
            logger.debug("Result %d: %s", idx, result)

        # Update original objects with results
        n_pairs = 0
        for signal_index, d_comp_pairs_attractors_by_value, n_signal_pairs in results:

            if signal_index not in signal_map:
                logger.error("Signal index %s not found in signal_map", signal_index)
                continue  # Skip this result if there is a problem

            o_output_signal = signal_map[signal_index]
            o_output_signal.d_comp_pairs_attractors_by_value = (
                d_comp_pairs_attractors_by_value
            )
            n_pairs += n_signal_pairs

        # Show the final result
        # print(f"Number of attractor pairs: {n_pairs}")
        CustomText.make_sub_sub_title("END FIND ATTRACTOR PAIRS")

    # SHOW FUNCTIONS
    def show_directed_edges(self) -> None:
        CustomText.print_duplex_line()
        logger.info("SHOW THE DIRECTED EDGES OF THE CBN")
        for o_directed_edge in self.l_directed_edges:
            o_directed_edge.show()

    def show_directed_edges_order(self) -> None:
        CustomText.print_duplex_line()
        logger.info(
            "SHOW THE EDGES %s",
            " ".join(
                f"{o_directed_edge.index}: {o_directed_edge.get_edge()}"
                for o_directed_edge in self.l_directed_edges
            ),
        )

    def show_coupled_signals_kind(self) -> None:
        CustomText.print_duplex_line()
        logger.info("SHOW THE COUPLED SIGNALS KINDS")
        n_restricted_signals = 0
        for o_directed_edge in self.l_directed_edges:
            logger.info(
                "SIGNAL: %s, RELATION: %s -> %s, KIND: %s - %s",
                o_directed_edge.index_variable,
                o_directed_edge.output_local_network,
                o_directed_edge.input_local_network,
                o_directed_edge.kind_signal,
                o_directed_edge.d_kind_signal[o_directed_edge.kind_signal],
            )
            if o_directed_edge.kind_signal == 1:
                n_restricted_signals += 1
        logger.info("Number of restricted signals: %d", n_restricted_signals)

    def show_description(self) -> None:
        CustomText.make_title("CBN description")
        l_local_networks_indexes = [
            o_local_network.index for o_local_network in self.l_local_networks
        ]
        CustomText.make_sub_title(f"Local Networks: {l_local_networks_indexes}")
        for o_local_network in self.l_local_networks:
            o_local_network.show()
        CustomText.make_sub_title(f"Directed edges: {l_local_networks_indexes}")
        # for o_directed_edge in self.l_directed_edges:
        #     o_directed_edge.show()

    def show_global_scenes(self) -> None:
        CustomText.make_sub_title("LIST OF GLOBAL SCENES")
        for o_global_scene in self.l_global_scenes:
            o_global_scene.show()

    def show_local_attractors(self) -> None:
        CustomText.make_title("Show local attractors")
        for o_local_network in self.l_local_networks:
            CustomText.make_sub_title(f"Network {o_local_network.index}")
            for o_scene in o_local_network.local_scenes:
                title = (
                    f"Network: {o_local_network.index} - Scene: {o_scene.l_values} - "
                    f"N. of Attractors: {len(o_scene.l_attractors)}"
                )
                CustomText.make_sub_sub_title(title)
                logger.info(
                    "Network: %s - Scene: %s", o_local_network.index, o_scene.l_values
                )
                logger.info("Attractors number: %d", len(o_scene.l_attractors))
                for o_attractor in o_scene.l_attractors:
                    CustomText.print_simple_line()
                    logger.info(
                        "Global index: %s -> %s",
                        o_attractor.g_index,
                        self.d_local_attractors[o_attractor.g_index],
                    )
                    for o_state in o_attractor.l_states:
                        logger.debug("%s", o_state.l_variable_values)

    def show_attractor_pairs(self) -> None:
        CustomText.print_duplex_line()
        logger.info("LIST OF THE COMPATIBLE ATTRACTOR PAIRS")

        total_pairs = 0  # Variable to keep track of the total pairs

        for o_directed_edge in self.l_directed_edges:
            CustomText.print_simple_line()
            logger.info(
                "Edge: %s -> %s",
                o_directed_edge.output_local_network,
                o_directed_edge.input_local_network,
            )

            for key in o_directed_edge.d_comp_pairs_attractors_by_value.keys():
                CustomText.print_simple_line()
                logger.info(
                    "Coupling Variable: %s, Scene: %s",
                    o_directed_edge.index_variable,
                    key,
                )

                for o_pair in o_directed_edge.d_comp_pairs_attractors_by_value[key]:
                    logger.debug("%s", o_pair)
                    total_pairs += 1  # Increment total pairs for each pair found
        logger.info("Total compatible attractor pairs: %d", total_pairs)

    def show_stable_attractor_fields(self) -> None:
        CustomText.print_duplex_line()
        logger.info("Show the list of attractor fields")
        logger.info("Number Stable Attractor Fields: %d", len(self.d_attractor_fields))
        for key, o_attractor_field in self.d_attractor_fields.items():
            CustomText.print_simple_line()
            logger.info("%s", key)
            logger.debug("%s", o_attractor_field)

    def show_resume(self) -> None:
        # Method to display a detailed summary of the CBN
        CustomText.make_title("CBN Detailed Resume")

        CustomText.make_sub_sub_title("Main Characteristics")
        CustomText.print_simple_line()
        logger = logging.getLogger(__name__)
        logger.info("Number of local networks: %d", len(self.l_local_networks))
        logger.info(
            "Number of variables per local network: %s", self.get_n_local_variables()
        )
        logger.info("Topology Type: %s", self.get_kind_topology())
        logger.info("Number of input variables: %s", self.get_n_input_variables())
        logger.info("Number of output variables: %s", self.get_n_output_variables())

        CustomText.make_sub_sub_title("Indicators")
        CustomText.print_simple_line()
        logger.info("Number of local attractors: %d", self.get_n_local_attractors())
        logger.info("Number of attractor pairs: %d", self.get_n_pair_attractors())
        logger.info("Number of attractor fields: %d", self.get_n_attractor_fields())
        CustomText.print_simple_line()

    def show_local_attractors_dictionary(self) -> None:
        # Method to display the dictionary of local attractors
        CustomText.make_title("Global Dictionary of Local Attractors")

        for key, value in self.d_local_attractors.items():
            logger.info("%s -> %s", key, value)

    def show_stable_attractor_fields_detailed(self) -> None:
        # Method to display stable attractor fields in detail
        CustomText.print_duplex_line()
        logger.info("Showing the list of attractor fields")
        logger.info(
            "Number of Stable Attractor Fields: %d", len(self.d_attractor_fields)
        )

        for key, value in self.d_attractor_fields.items():
            CustomText.print_simple_line()
            logger.info("%s -> %s", key, value)

            for i_attractor in value:
                logger.info(
                    "%s -> %s", i_attractor, self.d_local_attractors[i_attractor]
                )
                o_attractor = self.get_local_attractor_by_index(i_attractor)

                if o_attractor:
                    o_attractor.show()

    def show_attractor_fields(self) -> None:
        """
        Displays the attractor fields.

        This method prints a list of attractor fields and the total number found.

        Returns:
            None
        """
        CustomText.make_sub_title("List of attractor fields")
        for key, value in self.d_attractor_fields.items():
            logger.info("%s -> %s", key, value)
        logger.info(
            "Number of attractor fields found: %d", len(self.d_attractor_fields)
        )

    # GENERATE FUNCTIONS
    def generate_global_scenes(self) -> None:
        """
        Generates global scenes.

        This method creates all possible binary combinations for the directed edges
        and initializes GlobalScene objects.

        Returns:
            None
        """
        CustomText.make_title("Generated Global Scenes")
        l_edges_indexes = [
            o_directed_edge.index_variable for o_directed_edge in self.l_directed_edges
        ]
        binary_combinations = list(product([0, 1], repeat=len(l_edges_indexes)))
        self.l_global_scenes = [
            GlobalScene(l_edges_indexes, list(combination))
            for combination in binary_combinations
        ]
        CustomText.make_sub_title("Global Scenes generated")

    def plot_topology(self, ax=None) -> None:
        """
        Plots the network topology.

        This method calls the plotting function from the global topology object.

        Args:
            ax (matplotlib.axes._axes.Axes, optional): The axes on which to plot. Defaults to None.

        Returns:
            None
        """
        self.o_global_topology.plot_topology(ax=ax)

    def count_fields_by_global_scenes(self):
        """
        Counts stable attractor fields by global scenes.

        This method creates a dictionary mapping unique scene combinations
        to the number of stable attractor fields associated with them.

        Returns:
            None: The results are stored in `self.d_global_scenes_count`.
        """
        self.d_global_scenes_count: Dict[str, int] = {}

        for key, o_attractor_field in self.d_attractor_fields.items():
            d_variable_value = {}

            for i_attractor in o_attractor_field:
                o_attractor = self.get_local_attractor_by_index(i_attractor)
                if o_attractor:
                    for aux_pos, aux_variable in enumerate(o_attractor.relation_index):
                        d_variable_value[aux_variable] = o_attractor.local_scene[
                            aux_pos
                        ]

            # Generate a sorted key representing the scene combination
            sorted_dict = {k: d_variable_value[k] for k in sorted(d_variable_value)}
            combination_key = "".join(str(sorted_dict[k]) for k in sorted_dict)

            # Update the count of this specific scene combination
            if combination_key in self.d_global_scenes_count:
                self.d_global_scenes_count[combination_key] += 1
            else:
                self.d_global_scenes_count[combination_key] = 1

    # NEW GENERATOR
    @staticmethod
    def cbn_generator(
        v_topology: int,
        n_local_networks: int,
        n_vars_network: int,
        n_input_variables: int,
        n_output_variables: int,
        n_max_of_clauses: Optional[int] = None,
        n_max_of_literals: Optional[int] = None,
        n_edges: Optional[int] = None,
        coupling_strategy: CouplingStrategy = OrCoupling(),
    ) -> "CBN":
        """Factory method to generate a complete CBN from high-level parameters.

        This is the primary entry point for creating a CBN. It automates the
        entire construction process, including:
        1. Generating the global network topology (e.g., complete graph, cycle).
        2. Creating a template for the local networks' dynamics.
        3. Assembling the final CBN object with the specified coupling logic.

        Args:
            v_topology: An integer ID specifying the global network topology
                (e.g., 1 for 'complete', 3 for 'cycle').
            n_local_networks: The number of local networks in the CBN.
            n_vars_network: The number of variables within each local network.
            n_input_variables: The number of input signals each local network
                can receive.
            n_output_variables: The number of variables from a local network
                that are used to compute an output signal.
            n_max_of_clauses: The maximum number of clauses in the random
                CNF functions for local dynamics. Defaults to 2.
            n_max_of_literals: The maximum number of literals per clause in
                the random CNF functions. Defaults to 3.
            n_edges: The number of edges for topologies that require it (e.g.,
                aleatory graphs). Defaults to None.
            coupling_strategy: An instance of a `CouplingStrategy` subclass
                that defines the logic for combining output signals (e.g.,
                `OrCoupling()`, `AndCoupling()`). Defaults to `OrCoupling()`.

        Returns:
            An initialized `CBN` object ready for analysis.
        """

        # GENERATE THE GLOBAL TOPOLOGY
        o_global_topology = GlobalTopology.generate_sample_topology(
            v_topology=v_topology, n_nodes=n_local_networks, n_edges=n_edges
        )

        # GENERATE THE LOCAL NETWORK TEMPLATE
        o_template = LocalNetworkTemplate(
            n_vars_network=n_vars_network,
            n_input_variables=n_input_variables,
            n_output_variables=n_output_variables,
            n_max_of_clauses=n_max_of_clauses,
            n_max_of_literals=n_max_of_literals,
            v_topology=v_topology,
        )

        # GENERATE THE CBN WITH THE TOPOLOGY AND TEMPLATE
        o_cbn = CBN.generate_cbn_from_template(
            v_topology=v_topology,
            n_local_networks=n_local_networks,
            n_vars_network=n_vars_network,
            o_template=o_template,
            l_global_edges=o_global_topology.l_edges,
            coupling_strategy=coupling_strategy,
        )

        return o_cbn

    @staticmethod
    def find_output_edges_by_network_index(
        index: int, l_directed_edges: List["DirectedEdge"]
    ) -> List["DirectedEdge"]:
        """
        Finds all output edges for a given network index.

        Args:
            index (int): The index of the local network.
            l_directed_edges (List[DirectedEdge]): List of DirectedEdge objects.

        Returns:
            List[DirectedEdge]: List of DirectedEdge objects that are output edges for the specified network index.
        """
        return [edge for edge in l_directed_edges if edge.output_local_network == index]

    @staticmethod
    def find_input_edges_by_network_index(index, l_directed_edges):
        """
        Finds all input edges for a given network index.

        Args:
            index (int): The index of the local network.
            l_directed_edges (list): List of DirectedEdge objects.

        Returns:
            list: List of DirectedEdge objects that are input edges for the specified network index.
        """
        return [edge for edge in l_directed_edges if edge.input_local_network == index]

    @staticmethod
    def generate_local_networks_indexes_variables(n_local_networks, n_vars_network):
        """
        Generates local networks and their variable indexes.

        Args:
            n_local_networks (int): Number of local networks to generate.
            n_vars_network (int): Number of variables per network.

        Returns:
            list: List of LocalNetwork objects.
        """
        l_local_networks = []
        v_cont_var = 1
        for v_num_network in range(1, n_local_networks + 1):
            # generate the variables of the networks
            internal_variables = list(range(v_cont_var, v_cont_var + n_vars_network))
            # create the Local Network object
            o_local_network = LocalNetwork(
                index=v_num_network, internal_variables=internal_variables
            )
            # add the local network object to the list
            l_local_networks.append(o_local_network)
            # update the index of the variables
            v_cont_var += n_vars_network
        return l_local_networks

    @staticmethod
    def generate_cbn_from_template(
        v_topology, n_local_networks, n_vars_network, o_template, l_global_edges, coupling_strategy: CouplingStrategy
    ):
        """
        Generates a CBN (Coupled Boolean Network) using a given template and global edges.

        Args:
            v_topology: Topology of the CBN.
            n_local_networks (int): Number of local networks.
            n_vars_network (int): Number of variables per network.
            o_template: Template for local networks.
            l_global_edges (list): List of tuples representing the global edges between local networks.
            coupling_strategy (CouplingStrategy): The coupling strategy to use.

        Returns:
            A CBN object generated from the provided template and global edges.
        """

        # Generate the local networks with indexes and variables (without relations or dynamics)
        l_local_networks = CBN.generate_local_networks_indexes_variables(
            n_local_networks=n_local_networks, n_vars_network=n_vars_network
        )

        # Generate the directed edges between the local networks
        l_directed_edges = []

        # Get the last index of the variables for the indexes of the directed edges
        i_last_variable = l_local_networks[-1].internal_variables[-1] + 1

        # Generate the directed edges using the last variable generated and the selected output variables
        i_directed_edge = 1

        # Create a set of valid network indices for quick validation
        valid_network_indices = {net.index for net in l_local_networks}

        for relation in l_global_edges:
            output_local_network = relation[0]
            input_local_network = relation[1]

            # Validate that the network indices from the global edges are valid
            if output_local_network not in valid_network_indices:
                raise IndexError(
                    f"Invalid output_local_network index {output_local_network} in global_edges. "
                    f"Valid indices are: {sorted(list(valid_network_indices))}"
                )
            if input_local_network not in valid_network_indices:
                raise IndexError(
                    f"Invalid input_local_network index {input_local_network} in global_edges. "
                    f"Valid indices are: {sorted(list(valid_network_indices))}"
                )

            # Get the output variables from the template
            l_output_variables = o_template.get_output_variables_from_template(
                output_local_network, l_local_networks
            )

            # Generate the coupling function
            coupling_function = coupling_strategy.generate_coupling_function(l_output_variables)
            # Create the DirectedEdge object
            o_directed_edge = DirectedEdge(
                index=i_directed_edge,
                index_variable_signal=i_last_variable,
                input_local_network=input_local_network,
                output_local_network=output_local_network,
                l_output_variables=l_output_variables,
                coupling_function=coupling_function,
            )
            i_last_variable += 1
            i_directed_edge += 1
            # Add the DirectedEdge object to the list
            l_directed_edges.append(o_directed_edge)

        # Process the coupling signals for every local network
        for o_local_network in l_local_networks:
            # Find the input signals for each local network
            input_signals = CBN.find_input_edges_by_network_index(
                index=o_local_network.index, l_directed_edges=l_directed_edges
            )
            # Process the input signals of the local network
            o_local_network.process_input_signals(input_signals=input_signals)

        # Generate the dynamics of the local networks using the template
        l_local_networks = CBN.generate_local_dynamic_with_template(
            o_template=o_template,
            l_local_networks=l_local_networks,
            l_directed_edges=l_directed_edges,
        )

        # Integrate the CNF for the coupling logic
        for edge in l_directed_edges:
            # Generate the CNF clauses for the coupling function
            coupling_cnf = coupling_strategy.to_cnf(edge.l_output_variables, edge.index_variable)

            # Create an InternalVariable for the coupling signal
            coupling_variable = InternalVariable(index=edge.index_variable, cnf_function=coupling_cnf)

            # Find the source network and add the coupling logic to it
            for net in l_local_networks:
                if net.index == edge.output_local_network:
                    net.descriptive_function_variables.append(coupling_variable)
                    break

        # Generate the special Coupled Boolean Network (CBN)
        o_cbn = CBN(
            l_local_networks=l_local_networks, l_directed_edges=l_directed_edges
        )

        # Add the Global Topology Object
        o_global_topology = GlobalTopology(
            v_topology=v_topology, l_edges=l_global_edges
        )
        o_cbn.o_global_topology = o_global_topology

        return o_cbn

    @staticmethod
    def generate_local_dynamic_with_template(
        o_template, l_local_networks, l_directed_edges
    ):
        """
        Generates the dynamics for each local network using a given template and directed edges.

        Args:
            o_template: Template used to generate dynamics.
            l_local_networks (list): List of LocalNetwork objects to update.
            l_directed_edges (list): List of DirectedEdge objects for the connections between networks.

        Returns:
            list: Updated list of LocalNetwork objects with their dynamics.
        """
        # number_max_of_clauses and number_max_of_literals are intentionally
        # omitted because they are not used in this implementation.

        # List to store the updated local networks
        l_local_networks_updated = []

        # Update the dynamics for each local network
        for o_local_network in l_local_networks:
            # CustomText.print_simple_line()
            # print("Local Network:", o_local_network.index)

            # List to hold the function descriptions for the variables
            descriptive_function_variables = []

            # Generate clauses for each local network based on the template
            for i_local_variable in o_local_network.internal_variables:
                CustomText.print_simple_line()
                # Adapt the clause template to the 5_specific variable
                l_clauses_node = CBN.update_clause_from_template(
                    o_template=o_template,
                    l_local_networks=l_local_networks,
                    o_local_network=o_local_network,
                    i_local_variable=i_local_variable,
                    l_directed_edges=l_directed_edges,
                )

                # Create an InternalVariable object with the generated clauses
                o_variable_model = InternalVariable(
                    index=i_local_variable, cnf_function=l_clauses_node
                )
                # Add the variable model to the list
                descriptive_function_variables.append(o_variable_model)

            # Update the local network with the function descriptions
            o_local_network.descriptive_function_variables = (
                descriptive_function_variables.copy()
            )
            l_local_networks_updated.append(o_local_network)
            # print("Local network created:", o_local_network.index)
            # CustomText.print_simple_line()

        # Return the updated list of local networks
        return l_local_networks_updated

    @staticmethod
    def update_clause_from_template(
        o_template,
        l_local_networks,
        o_local_network,
        i_local_variable,
        l_directed_edges,
    ):
        """
        Updates the clauses from the template for a 5_specific variable in a local network.

        Args:
            o_template: The template containing CNF functions.
            l_local_networks (list): List of LocalNetwork objects.
            o_local_network: The 5_specific LocalNetwork object being updated.
            i_local_variable: The index of the local variable to update.
            l_directed_edges (list): List of DirectedEdge objects.

        Returns:
            list: Updated list of clauses for the local variable.
        """

        # Gather all index variables from directed edges
        # l_indexes_directed_edges was previously computed but not used.

        # Determine the CNF function index for the variable in the template
        n_local_variables = len(l_local_networks[0].internal_variables)
        i_template_variable = (
            i_local_variable
            - ((o_local_network.index - 1) * n_local_variables)
            + n_local_variables
        )
        pre_l_clauses_node = o_template.d_variable_cnf_function[i_template_variable]

        # print("Local Variable index:", i_local_variable)
        # print("Template Variable index:", i_template_variable)
        # print("Template Function:", pre_l_clauses_node)

        # Update the CNF function clauses with the 5_specific variable index
        l_clauses_node = []
        for pre_clause in pre_l_clauses_node:
            # Create a clause by updating variable indices
            l_clause = []
            for template_value in pre_clause:
                # Determine the sign of the variable
                b_symbol = True
                if template_value < 0:
                    b_symbol = False

                # Update the variable index
                local_value = (
                    abs(template_value)
                    + ((o_local_network.index - 3) * n_local_variables)
                    + n_local_variables
                )

                # Check if the variable is internal or external
                if local_value not in o_local_network.internal_variables:
                    # Use external variables if the local variable is not found
                    l_clause = o_local_network.external_variables
                    break

                # Add the sign to the value
                if not b_symbol:
                    local_value = -local_value

                # Append the value to the clause
                l_clause.append(local_value)

            # Append the updated clause to the list
            l_clauses_node.append(l_clause)

        # Remove empty clauses
        l_clauses_node = [clause for clause in l_clauses_node if clause]

        # print("Local Variable Index:", i_local_variable)
        # print("CNF Function:", l_clauses_node)

        return l_clauses_node

    # GETTERS FUNCTIONS
    def get_local_attractor_by_index(
        self, i_attractor: int
    ) -> Optional[LocalAttractor]:
        """
        Method to retrieve a local attractor by its index.

        Args:
            i_attractor (int): The index of the attractor to find.

        Returns:
            Optional[LocalAttractor]: The corresponding attractor if found, otherwise None.
        """
        for o_local_network in self.l_local_networks:
            for o_scene in o_local_network.local_scenes:
                for o_attractor in o_scene.l_attractors:
                    if o_attractor.g_index == i_attractor:
                        return o_attractor
        logger.error("Attractor index not found: %s", i_attractor)
        return None

    def get_kind_topology(self):
        return self.o_global_topology.v_topology

    def get_n_input_variables(self):
        pass

    def get_n_output_variables(self):
        pass

    def get_network_by_index(self, index: int) -> Optional[LocalNetwork]:
        for o_local_network in self.l_local_networks:
            if o_local_network.index == index:
                return o_local_network
        return None

    def get_input_edges_by_network_index(self, index: int) -> List[DirectedEdge]:
        return [
            o_directed_edge
            for o_directed_edge in self.l_directed_edges
            if o_directed_edge.input_local_network == index
        ]

    def get_output_edges_by_network_index(self, index: int) -> List[DirectedEdge]:
        return [
            o_directed_edge
            for o_directed_edge in self.l_directed_edges
            if o_directed_edge.output_local_network == index
        ]

    def get_index_networks(self) -> List[int]:
        return [i_network.l_index for i_network in self.l_local_networks]

    def get_attractors_by_input_signal_value(
        self, index_variable_signal: int, signal_value: int
    ) -> List[LocalAttractor]:
        l_attractors = []
        for o_local_network in self.l_local_networks:
            for scene in o_local_network.local_scenes:
                if (
                    scene.l_values is not None
                    and index_variable_signal in scene.l_index_signals
                ):
                    pos = scene.l_index_signals.index(index_variable_signal)
                    if scene.l_values[pos] == str(signal_value):
                        l_attractors.extend(scene.l_attractors)
        return l_attractors

    def get_n_local_attractors(self) -> int:
        return sum(
            len(o_scene.l_attractors)
            for o_local_network in self.l_local_networks
            for o_scene in o_local_network.local_scenes
        )

    def get_n_pair_attractors(self) -> int:
        return sum(
            len(o_directed_edge.d_comp_pairs_attractors_by_value[0])
            + len(o_directed_edge.d_comp_pairs_attractors_by_value[1])
            for o_directed_edge in self.l_directed_edges
        )

    def get_n_attractor_fields(self) -> int:
        return len(self.d_attractor_fields)

    def get_n_local_variables(self) -> int:
        return (
            len(self.l_local_networks[0].internal_variables)
            if self.l_local_networks
            else 0
        )

    def get_global_scene_attractor_fields(self):
        return self.d_global_scenes_count


# Backwards-compatible assignments: expose utility functions as CBN staticmethods
CBN.evaluate_pair = staticmethod(_evaluate_pair)
CBN.cartesian_product_mod = staticmethod(_cartesian_product_mod)
CBN.flatten = staticmethod(_flatten)
CBN._convert_to_tuple = staticmethod(_convert_to_tuple)
CBN.process_single_base_pair = staticmethod(_process_single_base_pair)
# Backwards-compatible alias for legacy method name
if not hasattr(CBN, "show_attractors_fields"):
    CBN.show_attractors_fields = CBN.show_attractor_fields

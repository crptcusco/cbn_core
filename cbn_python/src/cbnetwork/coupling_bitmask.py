"""
Module for Bitmask-based Coupling Functions.
"""

import random
from typing import List

from .coupling import CouplingStrategy


class CouplingFunction(CouplingStrategy):
    """
    Stores a coupling rule using a bitmask for the truth table.
    """

    def __init__(self, name: str, k_inputs: int, bitmask: int):
        """
        Initialize the CouplingFunction.

        Args:
            name (str): Name of the rule.
            k_inputs (int): Number of input variables.
            bitmask (int): Truth table represented as an integer.
        """
        self.name = name
        self.k_inputs = k_inputs
        self.bitmask = bitmask

    def evaluate(self, input_states: list[int]) -> int:
        """
        Evaluates the coupling function for the given input states.

        Args:
            input_states (list[int]): List of input values (0 or 1).

        Returns:
            int: The evaluated output (0 or 1).
        """
        index = 0
        for i, val in enumerate(input_states):
            if val:
                index |= 1 << i
        return (self.bitmask >> index) & 1

    def generate_coupling_function(self, output_variables: List[int]) -> str:
        """Generates a string representation of the bitmask function."""
        # For simplicity and parser compatibility, we return "0" or "1" if it's constant,
        # otherwise we return a placeholder that the parser should handle.
        # Since process_true_table uses self.bitmask if it's not None,
        # we provide a dummy string that the parser won't choke on.
        if self.k_inputs == 0:
            return "1" if self.bitmask & 1 else "0"

        # The parser expects A-Z for variables in the string, but we want
        # to ensure it doesn't fail. However, if bitmask is present,
        # process_true_table skips parsing. So we can return any valid string.
        # "A ∨ B ∨ ..." where the number of variables matches k_inputs.
        from string import ascii_uppercase
        l_vars = [ascii_uppercase[i] for i in range(min(self.k_inputs, 26))]
        return " ∨ ".join(l_vars)

    def to_cnf(
        self, output_variables: List[int], coupling_variable: int
    ) -> List[List[int]]:
        """
        Converts the bitmask logic into CNF.
        For bitmasks, we implement the logic C <=> TT[inputs].
        This is done by adding a clause for each False result (blocking the input)
        and each True result (implying the output).
        """
        clauses = []
        n = len(output_variables)

        for i in range(1 << n):
            # tt_val is the expected output for this input combination
            tt_val = (self.bitmask >> i) & 1

            # Input combination as literals
            # if bit j is 1, literal is Vj; if 0, literal is -Vj
            input_lits = []
            for j in range(n):
                if (i >> j) & 1:
                    input_lits.append(output_variables[j])
                else:
                    input_lits.append(-output_variables[j])

            if tt_val == 1:
                # (V1 & V2 & ... & Vn) => C  <=>  (-V1 | -V2 | ... | -Vn | C)
                clauses.append([-lit for lit in input_lits] + [coupling_variable])
            else:
                # (V1 & V2 & ... & Vn) => -C  <=>  (-V1 | -V2 | ... | -Vn | -C)
                clauses.append([-lit for lit in input_lits] + [-coupling_variable])

        return clauses

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation for JSON serialization.

        Returns:
            dict: The dictionary representation.
        """
        return {"type": self.name, "k_inputs": self.k_inputs, "bitmask": self.bitmask}


class CouplingFactory:
    """
    Factory for creating standard coupling functions.
    """

    @staticmethod
    def create_or_function(k: int) -> CouplingFunction:
        """Bitmask with all states 1 except the zero state."""
        bitmask = (1 << (1 << k)) - 2
        return CouplingFunction("OR", k, bitmask)

    @staticmethod
    def create_and_function(k: int) -> CouplingFunction:
        """Bitmask with only the last state (all inputs 1) set to 1."""
        bitmask = 1 << ((1 << k) - 1)
        return CouplingFunction("AND", k, bitmask)

    @staticmethod
    def create_majority_function(k: int) -> CouplingFunction:
        """Bitmask where the state is 1 if more than half of the inputs are active."""
        bitmask = 0
        for i in range(1 << k):
            # Count set bits in i
            count = bin(i).count("1")
            if count > k / 2:
                bitmask |= 1 << i
        return CouplingFunction("MAJORITY", k, bitmask)

    @staticmethod
    def create_mixed_random_function(k: int) -> CouplingFunction:
        """Random bitmask to simulate complex/mixed dynamics."""
        bitmask = random.getrandbits(1 << k)
        return CouplingFunction("MIXED_RANDOM", k, bitmask)

    @staticmethod
    def create_buffer_function() -> CouplingFunction:
        """1 input, output is same as input (Buffer)."""
        return CouplingFunction("BUFFER", 1, 2)

"""
Module for Bitmask-based Coupling Functions.
"""

import random


class CouplingFunction:
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

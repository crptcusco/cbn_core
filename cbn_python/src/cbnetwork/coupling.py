"""
This module defines the coupling strategies for Coupled Boolean Networks (CBNs).

It provides a flexible way to define the logical relationship between local networks
through the `CouplingStrategy` abstract base class and its concrete implementations.
"""
from abc import ABC, abstractmethod
from itertools import combinations
from typing import List


class CouplingStrategy(ABC):
    """Abstract base class for defining coupling strategies in a CBN.

    A coupling strategy defines the logical function that combines the output
    variables from one local network to create a single coupling signal that
    is used as an input to another local network.
    """

    @abstractmethod
    def generate_coupling_function(self, output_variables: List[int]) -> str:
        """Generates a string representation of the coupling function.

        Args:
            output_variables (List[int]): A list of the output variable indices.

        Returns:
            str: A string representing the logical function (e.g., "v1 ∨ v2").
        """
        pass

    @abstractmethod
    def to_cnf(
        self, output_variables: List[int], coupling_variable: int
    ) -> List[List[int]]:
        """Converts the coupling logic into Conjunctive Normal Form (CNF).

        The CNF representation is necessary for the SAT solver. This method
        returns a list of clauses, where each clause is a list of literals.
        For example, (A ∨ ¬B) ∧ C would be [[A, -B], [C]].

        Args:
            output_variables (List[int]): A list of the output variable indices.
            coupling_variable (int): The index of the variable representing the
                coupling signal.

        Returns:
            List[List[int]]: A list of clauses representing the CNF.
        """
        pass


class OrCoupling(CouplingStrategy):
    """Represents a disjunctive (OR) coupling.

    The coupling signal is active if at least one of the output variables is active.
    """

    def generate_coupling_function(self, output_variables: List[int]) -> str:
        """Generates an OR function string, e.g., 'v1 ∨ v2'."""
        return " " + " ∨ ".join(map(str, output_variables)) + " "

    def to_cnf(
        self, output_variables: List[int], coupling_variable: int
    ) -> List[List[int]]:
        """Converts the OR logic to CNF.

        The logical equivalence C <=> (V1 ∨ V2 ∨ ... ∨ Vn) is converted to
        a set of clauses that is logically equivalent and suitable for a SAT solver.

        Args:
            output_variables (List[int]): The list of variables V1, V2, ...
            coupling_variable (int): The variable C representing the output.

        Returns:
            List[List[int]]: The CNF clauses.
        """
        clauses = []
        # Implication: (Vi => C) for all i, which is (¬Vi ∨ C)
        for var in output_variables:
            clauses.append([-var, coupling_variable])

        # Implication: C => (V1 ∨ V2 ∨ ...), which is (¬C ∨ V1 ∨ V2 ∨ ...)
        clauses.append(output_variables + [-coupling_variable])

        return clauses


class AndCoupling(CouplingStrategy):
    """Represents a conjunctive (AND) coupling.

    The coupling signal is active only if all output variables are active.
    """

    def generate_coupling_function(self, output_variables: List[int]) -> str:
        """Generates an AND function string, e.g., 'v1 ∧ v2'."""
        return " " + " ∧ ".join(map(str, output_variables)) + " "

    def to_cnf(
        self, output_variables: List[int], coupling_variable: int
    ) -> List[List[int]]:
        """Converts the AND logic to CNF.

        The logical equivalence C <=> (V1 ∧ V2 ∧ ... ∧ Vn) is converted.

        Args:
            output_variables (List[int]): The list of variables V1, V2, ...
            coupling_variable (int): The variable C representing the output.

        Returns:
            List[List[int]]: The CNF clauses.
        """
        clauses = []
        # Implication: (C => Vi) for all i, which is (¬C ∨ Vi)
        for var in output_variables:
            clauses.append([var, -coupling_variable])

        # Implication: (V1 ∧ V2 ∧ ...) => C, which is (¬V1 ∨ ¬V2 ∨ ... ∨ C)
        negated_vars = [-var for var in output_variables]
        clauses.append(negated_vars + [coupling_variable])

        return clauses


class ThresholdCoupling(CouplingStrategy):
    """Represents a threshold coupling.

    The coupling signal is active if at least `k` of the output variables are active.

    Attributes:
        threshold (int): The minimum number of active inputs required to activate
            the coupling signal.
    """

    def __init__(self, threshold: int):
        """Initializes the ThresholdCoupling strategy.

        Args:
            threshold (int): The activation threshold. Must be a positive integer.

        Raises:
            ValueError: If the threshold is not a positive integer.
        """
        if threshold <= 0:
            raise ValueError("Threshold must be a positive integer.")
        self.threshold = threshold

    def generate_coupling_function(self, output_variables: List[int]) -> str:
        """Generates a threshold function string, e.g., 'Threshold(2, {v1, v2})'."""
        return f" Threshold({self.threshold}, {{{', '.join(map(str, output_variables))}}}) "

    def to_cnf(
        self, output_variables: List[int], coupling_variable: int
    ) -> List[List[int]]:
        """Converts the threshold logic "at least k out of n" to CNF.

        This implements the logic C <=> (sum(Vi) >= k).

        Warning:
            This method uses `itertools.combinations` to generate clauses. For a
            large number of inputs (n) or a moderate threshold (k), this can

            lead to a combinatorial explosion in the number of clauses, impacting
            performance.

        Args:
            output_variables (List[int]): The list of variables V1, V2, ...
            coupling_variable (int): The variable C representing the output.

        Returns:
            List[List[int]]: The CNF clauses.
        """
        n = len(output_variables)
        k = self.threshold
        clauses = []

        if k > n:
            # The threshold can never be met, so C must be false.
            return [[-coupling_variable]]

        # Implication 1: (sum(Vi) >= k) => C
        # If any k variables are true, C must be true.
        # This is encoded as (¬V_i1 ∨ ¬V_i2 ∨ ... ∨ ¬V_ik ∨ C) for all combinations of k vars.
        for combo in combinations(output_variables, k):
            clauses.append([-v for v in combo] + [coupling_variable])

        # Implication 2: C => (sum(Vi) >= k)
        # If C is true, you cannot have (n-k+1) variables that are false.
        # Clause: (¬C ∨ V_i1 ∨ V_i2 ∨ ... ∨ V_i(n-k+1))
        for combo in combinations(output_variables, n - k + 1):
            clauses.append([-coupling_variable] + list(combo))

        return clauses

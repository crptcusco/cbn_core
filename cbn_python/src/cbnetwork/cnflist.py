import random


class CNFList:
    @staticmethod
    def generate_cnf(l_inter_vars, input_coup_sig_index, max_clauses=2, max_literals=3):
        """
        Generates a robust CNF (Conjunctive Normal Form) list with random clauses.

        This function includes a retry mechanism to ensure that it always returns a
        valid, non-empty CNF list, preventing runtime errors from failed generation.

        Args:
            l_inter_vars (list): List of internal variables.
            input_coup_sig_index (int): Index of the input coupling signal.
            max_clauses (int): Maximum number of clauses to generate.
            max_literals (int): Maximum number of literals per clause.

        Returns:
            list: List of clauses in CNF format.

        Raises:
            RuntimeError: If a valid CNF function cannot be generated after a
                          set number of attempts.
        """
        max_attempts = 100  # Safety break to prevent potential infinite loops
        for _ in range(max_attempts):
            num_clauses = random.randint(
                1, max_clauses
            )
            l_cnf = []

            # Generate the clause for external signals
            if input_coup_sig_index is not None:
                var = input_coup_sig_index
                if random.choice([True, False]):
                    var = -var
                l_cnf.append([var])

            for _ in range(num_clauses):
                clause: list = []
                # Ensure max_literals does not exceed available variables
                effective_max_literals = min(max_literals, len(l_inter_vars))

                # Prevent empty l_inter_vars from causing an infinite loop
                if not l_inter_vars:
                    break

                # Use random.sample to avoid duplicate variables in a clause from the start
                num_literals = random.randint(1, effective_max_literals)
                clause_vars = random.sample(l_inter_vars, num_literals)

                clause = [
                    -var if random.choice([True, False]) else var
                    for var in clause_vars
                ]

                # Remove redundant literals within the clause (e.g., [A, -A])
                clause = CNFList.simplify_clause(clause)

                if clause:
                    l_cnf.append(clause)

            # Post-processing
            l_cnf = [c for c in l_cnf if c]  # Remove any empty clauses that slipped through
            l_cnf = CNFList.remove_duplicates(l_cnf)

            # If we have a valid CNF, return it
            if l_cnf:
                return l_cnf

        # If we've exhausted all attempts and still have no CNF, raise an error
        raise RuntimeError(f"Failed to generate a valid CNF function after {max_attempts} attempts.")

    @staticmethod
    def simplify_clause(clause):
        """
        Simplifies a clause by removing duplicate and complementary literals.

        Args:
            clause (list): List of literals in a clause.

        Returns:
            list: Simplified clause.
        """
        # Remove duplicate literals
        clause = list(set(clause))

        # Check for complementary literals (e.g., x and -x) and remove both
        simplified_clause = []
        for literal in clause:
            if -literal not in clause:
                simplified_clause.append(literal)

        return simplified_clause

    @staticmethod
    def remove_duplicates(l_cnf):
        """
        Removes duplicate clauses from the CNF list.

        Args:
            l_cnf (list): List of clauses in CNF format.

        Returns:
            list: List of unique clauses.
        """
        # Convert each clause to a tuple and create a set to remove duplicates
        unique_clauses = set(tuple(sorted(clause)) for clause in l_cnf)
        # Convert the unique tuples back to lists
        return [list(clause) for clause in unique_clauses]

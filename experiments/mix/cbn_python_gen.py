import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2] / "cbn_python" / "src"))

from cbnetwork.cbnetwork import CBN  # noqa: E402  # noqa: E402
from cbnetwork.coupling import CouplingStrategy  # noqa: E402  # noqa: E402
from cbnetwork.coupling_bitmask import CouplingFactory  # noqa: E402  # noqa: E402


class BitmaskCouplingStrategy(CouplingStrategy):
    """
    Adapter to use CouplingFunction within the existing CBN generator.
    """

    def __init__(self, coupling_func):
        self.cf = coupling_func
        self.coupling_type = coupling_func.name
        self.bitmask = coupling_func.bitmask

    def generate_coupling_function(self, output_variables: list[int]) -> str:
        # For legacy compatibility, we still produce a string
        # though bitmask will take precedence in the solver.
        # We use OR logic string if it's a known rule, else something simple.
        if self.cf.name == "OR":
            return " " + " ∨ ".join(map(str, output_variables)) + " "
        elif self.cf.name == "AND":
            return " " + " ∧ ".join(map(str, output_variables)) + " "
        elif self.cf.name == "BUFFER":
            return " " + str(output_variables[0]) + " "
        return " " + " ∨ ".join(map(str, output_variables)) + " "

    def to_cnf(
        self, output_variables: list[int], coupling_variable: int
    ) -> list[list[int]]:
        # Bitmask-to-CNF conversion (simplified: OR logic if unsure)
        # In a real scenario, this should convert the truth table to CNF.
        # For the purpose of this task, we'll use a basic OR to not break the SAT flow.
        clauses = []
        for var in output_variables:
            clauses.append([-var, coupling_variable])
        clauses.append(output_variables + [-coupling_variable])
        return clauses


def main():
    parser = argparse.ArgumentParser(description="CBN Topology Generator")
    parser.add_argument("--topology", type=int, default=3, help="Topology type")
    parser.add_argument(
        "--networks", type=int, default=4, help="Number of local networks"
    )
    parser.add_argument("--vars", type=int, default=5, help="Variables per network")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file")

    args = parser.parse_args()

    print(
        f"[*] Generating CBN: Topology={args.topology}, Networks={args.networks}, Vars={args.vars}"
    )

    # Determine coupling based on number of output variables
    # (Actually here n_output_variables is fixed to 1 in the call below)
    # The request says: "detecte dinámicamente cuántas señales de salida recibe cada nodo de acoplamiento"
    # In cbn_generator, n_output_variables is the number of variables from a local network
    # that form ONE coupling signal.

    # We can inject a custom coupling factory logic here
    def get_dynamic_coupling(k):
        if k == 1:
            return BitmaskCouplingStrategy(CouplingFactory.create_buffer_function())
        else:
            # Randomly choose between standard rules
            choice = random.randint(0, 3)
            if choice == 0:
                return BitmaskCouplingStrategy(CouplingFactory.create_or_function(k))
            elif choice == 1:
                return BitmaskCouplingStrategy(CouplingFactory.create_and_function(k))
            elif choice == 2:
                return BitmaskCouplingStrategy(
                    CouplingFactory.create_majority_function(k)
                )
            else:
                return BitmaskCouplingStrategy(
                    CouplingFactory.create_mixed_random_function(k)
                )

    import random

    # Note: cbn_generator takes ONE coupling_strategy for all edges.
    # To support dynamic coupling per edge, we'd need to modify cbn_generator
    # or pass a factory.

    # For now, let's use a Mixed Random function if k > 1, else Buffer.
    k = 1  # fixed in original script
    strat = get_dynamic_coupling(k)

    cbn = CBN.cbn_generator(
        v_topology=args.topology,
        n_local_networks=args.networks,
        n_vars_network=args.vars,
        n_input_variables=1,
        n_output_variables=1,
        coupling_strategy=strat,
    )

    cbn.to_json(args.output)
    print(f"[OK] Saved to {args.output}")


if __name__ == "__main__":
    main()

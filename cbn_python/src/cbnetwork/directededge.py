# external imports
import logging
import operator
import re
from collections import namedtuple
from itertools import product
from string import ascii_lowercase, ascii_uppercase

# local imports
from .utils.customtext import CustomText
from .utils.logging_config import setup_logging

setup_logging()


class DirectedEdge:
    def __init__(
        self,
        index,
        index_variable_signal,
        input_local_network,
        output_local_network,
        l_output_variables,
        coupling_function,
    ):
        """
        Initialize a DirectedEdge instance.

        Args:
            index (int): The index of the directed edge.
            index_variable_signal (int): The index of the variable signal.
            input_local_network (int): The index of the input local network.
            output_local_network (int): The index of the output local network.
            l_output_variables (list): List of output variables.
            coupling_function (str): The coupling function.
        """
        self.index = index
        self.index_variable = index_variable_signal
        self.input_local_network = input_local_network
        self.output_local_network = output_local_network
        self.l_output_variables = l_output_variables
        self.coupling_function = coupling_function

        # Calculated properties
        # True table for signal with the output variables
        self.true_table = self.process_true_table()
        # Dictionary for kind status of the signal
        self.d_kind_signal = {
            1: "RESTRICTED",
            2: "NOT COMPUTE",
            3: "STABLE",
            4: "NOT STABLE",
        }
        # Define the initial kind for every coupling signal
        self.kind_signal = 2
        # Dictionary for grouping attractors by their output signal value
        self.d_out_value_to_attractor: dict = {1: [], 0: []}
        # List of compatible pair attractors
        self.d_comp_pairs_attractors_by_value: dict = {0: [], 1: []}

    def show(self):
        """
        Display the details of the DirectedEdge instance.

        This method prints out information about the directed edge, including its index, the relationship between
        the input and output local networks, the variable index, the list of output variables, the coupling function,
        the truth table, and the kind of signal.
        """
        # Print the header with detailed information about the edge
        CustomText.make_sub_sub_title(
            f"Index Edge: {self.index} - "
            f"Relation: {self.output_local_network} -> {self.input_local_network} - "
            f"Variable: {self.index_variable}"
        )

        # Print the list of output variables and the coupling function
        logger = logging.getLogger(__name__)
        logger.info(
            "Variables: %s , Coupling Function: %s",
            self.l_output_variables,
            self.coupling_function,
        )

        logger.info("Truth table: %s", self.true_table)
        logger.info(
            "Kind signal: %s - %s",
            self.kind_signal,
            self.d_kind_signal[self.kind_signal],
        )

    def show_short(self):
        logging.getLogger(__name__).info(
            "%s , %s", self.output_local_network, self.input_local_network
        )

    def get_edge(self):
        return self.output_local_network, self.input_local_network

    def process_true_table(self):
        """
        Generates the truth table for the Boolean formula represented by the coupling function.

        This method parses the Boolean formula, evaluates it for all possible permutations of output variables,
        and constructs a truth table mapping input combinations to their corresponding output values.
        """
        r_true_table = {}  # Dictionary to store the truth table results

        # Tokenization
        # Regular expression to match tokens in the Boolean formula
        TOKEN_RE = re.compile(r"\s*(?:([A-Za-z01()~∧∨→↔])|(\S))")
        TOKEN_END = "<end of input>"  # Special token indicating the end of input

        def tokenize(s):
            """Generate tokens from the string s, followed by TOKEN_END."""
            for match in TOKEN_RE.finditer(s):
                token, error = match.groups()
                if token:
                    yield token
                else:
                    raise SyntaxError("Unexpected character {!r}".format(error))
            yield TOKEN_END

        # Parsing
        # Define structures for the parse tree
        Constant = namedtuple("Constant", "value")
        Variable = namedtuple("Variable", "name")
        UnaryOp = namedtuple("UnaryOp", "op operand")
        BinaryOp = namedtuple("BinaryOp", "left op right")

        # Tokens representing Boolean constants (0=False, 1=True).
        CONSTANTS = "01"

        # Tokens representing variables.
        VARIABLES = set(ascii_lowercase) | set(ascii_uppercase)

        # Unary and binary operators
        UNARY_OPERATORS = {
            "~": operator.not_,
        }
        BINARY_OPERATORS = {
            "∧": operator.and_,
            "∨": operator.or_,
            "→": lambda a, b: not a or b,
            "↔": operator.eq,
        }

        def parse(s):
            """Parse s as a Boolean expression and return the parse tree."""
            tokens = tokenize(s)  # Stream of tokens.
            token = next(tokens)  # The current token.

            def error(expected):
                raise SyntaxError("Expected {} but found {!r}".format(expected, token))

            def match(valid_tokens):
                nonlocal token
                if token in valid_tokens:
                    token = next(tokens)
                    return True
                else:
                    return False

            def term():
                t = token
                if match(VARIABLES):
                    return Variable(name=t)
                elif match(CONSTANTS):
                    return Constant(value=(t == "1"))
                elif match("("):
                    tree = disjunction()
                    if match(")"):
                        return tree
                    else:
                        error("')'")
                else:
                    error("term")

            def unary_expr():
                t = token
                if match("~"):
                    operand = unary_expr()
                    return UnaryOp(op=UNARY_OPERATORS[t], operand=operand)
                else:
                    return term()

            def binary_expr(parse_left, valid_operators, parse_right):
                left = parse_left()
                t = token
                if match(valid_operators):
                    right = parse_right()
                    return BinaryOp(left=left, op=BINARY_OPERATORS[t], right=right)
                else:
                    return left

            def implication():
                return binary_expr(unary_expr, "→↔", implication)

            def conjunction():
                return binary_expr(implication, "∧", conjunction)

            def disjunction():
                return binary_expr(conjunction, "∨", disjunction)

            tree = disjunction()
            if token != TOKEN_END:
                error("end of input")
            return tree

        def evaluate(tree, env):
            """Evaluate the expression in the parse tree.

            The environment maps variable names to their values.
            """
            if isinstance(tree, Constant):
                return tree.value
            elif isinstance(tree, Variable):
                return env[tree.name]
            elif isinstance(tree, UnaryOp):
                return tree.op(evaluate(tree.operand, env))
            elif isinstance(tree, BinaryOp):
                return tree.op(evaluate(tree.left, env), evaluate(tree.right, env))
            else:
                raise TypeError(f"Expected tree, found {type(tree)!r}")

        # Create a dictionary for each variable in the output set
        l_abecedario = list(ascii_uppercase)
        dict_aux_var_saida = {}
        cont_aux_abecedario = 0
        for variable_saida in self.l_output_variables:
            dict_aux_var_saida[" " + str(variable_saida) + " "] = l_abecedario[
                cont_aux_abecedario
            ]
            cont_aux_abecedario += 1

        # Generate all permutations of the output signals
        l_permutations = list(
            product([True, False], repeat=len(self.l_output_variables))
        )

        # Process each permutation to evaluate the Boolean formula
        for c_permutation in l_permutations:
            aux_dictionary = dict(zip(dict_aux_var_saida.values(), c_permutation))
            aux_coupling_function = self.coupling_function
            for aux_element in dict_aux_var_saida.keys():
                aux_coupling_function = aux_coupling_function.replace(
                    str(aux_element), str(dict_aux_var_saida[aux_element])
                )
            # Create the key for the truth table
            aux_key = "".join("1" if v else "0" for v in c_permutation)
            if evaluate(parse(aux_coupling_function), aux_dictionary):
                r_true_table[aux_key] = "1"
            else:
                r_true_table[aux_key] = "0"

        return r_true_table

    def show_dict_v_output_signal_attractor(self):
        """
        Display the dictionary mapping output signal values to their attractors.

        This method prints each output signal value and the corresponding list of attractors from the dictionary.
        """
        logger = logging.getLogger(__name__)
        for signal_value, l_attractors in self.d_out_value_to_attractor.items():
            logger.info("%s - %s", signal_value, l_attractors)

    def show_v_output_signal_attractor(self):
        """
        Display the output signal values and their corresponding attractors.

        This method prints each output signal value followed by a detailed list of attractors.
        For each attractor, it calls its `show` method to display its details.
        """
        logger = logging.getLogger(__name__)
        for signal_value, l_attractors in self.d_out_value_to_attractor.items():
            logger.info("Output signal Value - %s - Attractors:", signal_value)
            for o_attractor in l_attractors:
                o_attractor.show()

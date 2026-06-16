class InternalVariable:
    def __init__(self, index, cnf_function):
        """
        Initialize an InternalVariable object.

        Args:
            index (int): The index of the variable.
            cnf_function (list): The CNF (Conjunctive Normal Form) function associated with the variable.
        """
        self.index = int(index)
        self.cnf_function = cnf_function

    def show(self):
        """
        Display the details of the InternalVariable object.

        Prints the index of the variable and its CNF function.
        """
        import logging

        from .utils.logging_config import setup_logging

        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Variable Index: %s -> CNF : %s", self.index, self.cnf_function)

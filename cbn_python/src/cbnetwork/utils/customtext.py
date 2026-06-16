import logging

from .logging_config import setup_logging

setup_logging()


class CustomText:
    @staticmethod
    def print_duplex_line():
        """Log a line of equal signs for separation or emphasis."""
        logging.getLogger(__name__).info("%s", "=" * 50)

    @staticmethod
    def print_simple_line():
        """Log a simple line of hyphens for separation or emphasis."""
        logging.getLogger(__name__).info("%s", "-" * 50)

    @staticmethod
    def print_message(message, show):
        """Log a message if the 'show' parameter is True."""
        if show:
            logging.getLogger(__name__).info("%s", message)

    @staticmethod
    def print_stars():
        """Log a line of asterisks for separation or emphasis."""
        logging.getLogger(__name__).info("%s", "*" * 50)

    @staticmethod
    def print_dollars():
        """Log a line of dollar signs for separation or emphasis."""
        logging.getLogger(__name__).info("%s", "$" * 50)

    @staticmethod
    def make_principal_title(title):
        """Log a principal title surrounded by dollar signs."""
        logger = logging.getLogger(__name__)
        logger.info("%s", "$" * 50)
        logger.info("%s", title.upper())

    @staticmethod
    def make_title(title):
        """Log a title surrounded by asterisks."""
        logger = logging.getLogger(__name__)
        logger.info("%s", "*" * 50)
        logger.info("%s", title.upper())

    @staticmethod
    def make_sub_title(sub_title):
        """Log a subtitle surrounded by equal signs."""
        logger = logging.getLogger(__name__)
        logger.info("%s", "=" * 50)
        logger.info("%s", sub_title.upper())

    @staticmethod
    def make_sub_sub_title(sub_sub_title):
        """Log a sub-subtitle surrounded by hyphens."""
        logger = logging.getLogger(__name__)
        logger.info("%s", "-" * 50)
        logger.info("%s", sub_sub_title)

    @staticmethod
    def send_warning(message):
        """Log a warning message."""
        logging.getLogger(__name__).warning("WARNING: %s", message)

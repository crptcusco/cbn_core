import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure basic logging for the package if not already configured.

    This is idempotent: it will not reconfigure logging if handlers are present.
    """
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level, format="%(asctime)s %(levelname)s:%(name)s:%(message)s"
        )

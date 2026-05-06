from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure a simple stdout logger for the application.

    The format is intentionally compact so the logs stay readable in local
    development, terminals, and deployment logs.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

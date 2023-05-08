"""
This file contains the pipeline logger
"""
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger():
    logger = logging.getLogger(__name__)
    return logger

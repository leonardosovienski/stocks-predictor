"""predictor-core.obs — observabilidade: logging estruturado."""
import logging
import sys


def setup_logging(level: str = "INFO", fmt: str | None = None) -> None:
    fmt = fmt or "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
    logging.basicConfig(stream=sys.stdout, level=getattr(logging, level.upper()),
                        format=fmt, datefmt="%Y-%m-%dT%H:%M:%S")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

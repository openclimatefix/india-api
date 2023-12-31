"""Logging configuration for the application."""

import logging
import os
import sys

import structlog

# Set the log level
LOGLEVEL = os.getenv("LOGLEVEL", "INFO").upper()
_nameToLevel = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}

shared_processors = [
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.CallsiteParameterAdder(
        [
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.LINENO,
        ],
    ),
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
]

if sys.stderr.isatty():
    # Pretty printing when we run in a terminal session.
    # Automatically prints pretty tracebacks when "rich" is installed
    processors = [
        *shared_processors,
        structlog.dev.ConsoleRenderer(),
    ]

else:
    # Print JSON when we run, e.g., in a Docker container.
    # Also print structured tracebacks.
    processors = [
        *shared_processors,
        structlog.processors.EventRenamer("message", replace_by="_event"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(sort_keys=True),
    ]

# Add required processors and formatters to structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(_nameToLevel[LOGLEVEL]),
    processors=processors,
)


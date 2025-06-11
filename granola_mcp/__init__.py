"""
GranolaMCP - A Python library for interfacing with Granola.ai meeting data.

This library provides tools to access and process Granola.ai meeting data from
JSON cache files using 100% native Python with no external dependencies.
"""

__version__ = "0.1.0"
__author__ = "GranolaMCP Team"

from .core.parser import GranolaParser
from .core.meeting import Meeting
from .core.transcript import Transcript

__all__ = [
    "GranolaParser",
    "Meeting",
    "Transcript",
]
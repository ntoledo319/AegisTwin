"""
API package for the Advanced Data Analysis & Digital Twin System.
"""

from .main import app
from . import routes
from . import middleware

__all__ = [
    'app',
    'routes',
    'middleware',
]
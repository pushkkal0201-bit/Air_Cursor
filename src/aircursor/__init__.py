"""AirCursor 2.0 package."""

__version__ = "2.0.0"

from .server import create_app

__all__ = ["create_app", "__version__"]

"""slzmcp - Simple MCP server and client example"""

__version__ = "0.1.0"

from .server import mcp
from .client import main as run_client

__all__ = ["mcp", "run_client"]

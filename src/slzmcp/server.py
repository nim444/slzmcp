from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "slzmcp-server",
    host="127.0.0.1",
    port=8000,
)

@mcp.tool()
def echo(message: str) -> str:
    """Echo back the message"""
    return f"Echo: {message}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

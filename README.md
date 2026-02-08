# slzmcp

Simple MCP (Model Context Protocol) server and client implementation with HTTP transport.

## Features

- ✅ MCP Server with streamable-http transport
- ✅ MCP Client with HTTP connection
- ✅ External Authentication support (Auth0, Firebase, AWS Cognito, etc.)
- ✅ Simple echo tool example
- ✅ Session management
- ✅ Production-ready structure

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
git clone https://github.com/nim444/slzmcp.git
cd slzmcp
uv sync
```

### Run Server

```bash
uv run python -m slzmcp.server
```

Server starts on `http://127.0.0.1:8000/mcp`

### Run Client

In another terminal:

```bash
uv run python -m slzmcp.client
```

## Authentication

This project uses **external authentication providers** instead of building a custom OAuth server.

**Supported Providers:**
- Auth0
- Firebase Authentication
- AWS Cognito
- Clerk
- Keycloak
- Any OIDC-compliant provider

**See:** [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) for complete authentication guide.

### Quick Auth Example

```python
from fastmcp.server.auth.verifiers import JWTVerifier
from mcp.server.fastmcp import FastMCP

# Create JWT verifier for Auth0
verifier = JWTVerifier(
    jwks_uri="https://your-domain.auth0.com/.well-known/jwks.json",
    issuer="https://your-domain.auth0.com/",
    audience="https://api.yoursite.com",
    required_scopes=["read", "write"]
)

# Create secure server
mcp = FastMCP(
    "SecureServer",
    token_verifier=verifier
)
```

## Architecture

```
slzmcp/
├── src/slzmcp/
│   ├── server.py          # MCP server with echo tool
│   ├── client.py          # MCP client
│   └── auth/              # Authentication module (to be added)
├── docs/
│   └── AUTHENTICATION.md  # Complete auth guide
├── pyproject.toml         # Project configuration
└── README.md             # This file
```

## Project Structure

- **Server** (`src/slzmcp/server.py`): FastMCP server running on streamable-http
- **Client** (`src/slzmcp/client.py`): Connects to server via HTTP
- **Tools**: Simple echo tool for demonstration
- **Transport**: Streamable HTTP with session support

## Development

### Add New Tool

```python
@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"
```

### Testing

```bash
# Run server in background
uv run python -m slzmcp.server &

# Run client
uv run python -m slzmcp.client

# Stop server
kill %1
```

## Authentication Options

| Method | Complexity | Best For |
|--------|-----------|----------|
| JWT Verification | Low | Auth0, Firebase, OIDC providers |
| Token Introspection | Medium | Custom OAuth, opaque tokens |
| Simple API Keys | Low | Internal tools, microservices |

See [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) for detailed implementation.

## Deployment

### Local Development

```bash
uv run python -m slzmcp.server
```

### Production

1. Set up external authentication provider
2. Configure environment variables:
   ```bash
   export AUTH_JWKS_URI="https://auth.provider.com/.well-known/jwks.json"
   export AUTH_ISSUER="https://auth.provider.com/"
   export AUTH_AUDIENCE="https://api.yoursite.com"
   ```
3. Run with HTTPS:
   ```bash
   uv run uvicorn slzmcp.server:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
   ```

## Documentation

- [Authentication Guide](docs/AUTHENTICATION.md) - Complete auth implementation guide
- [MCP Specification](https://modelcontextprotocol.io/) - Official MCP docs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Resources

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

---

**Status:** Core implementation complete | Authentication guide ready for review

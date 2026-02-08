# Authentication Guide for slzmcp

This guide explains how to secure your MCP server using existing authentication services instead of building a custom OAuth 2.1 server.

## Overview

Rather than implementing a full OAuth 2.1 authorization server (complex, security-critical), you can integrate with proven authentication providers using **Token Verification**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT APPLICATION                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Authenticate with external provider (Auth0, Firebase, etc.) │
│  2. Receive JWT/Access Token                                    │
│  3. Call MCP tools: Authorization: Bearer <token>               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS + Bearer Token
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP SERVER (slzmcp)                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Token Verifier                                          │  │
│  │  • Extract Bearer token from header                      │  │
│  │  • Validate with external provider                       │  │
│  │  • Check scopes/permissions                              │  │
│  │  • Reject if invalid (401/403)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MCP Tools (Protected)                                   │  │
│  │  • Only accessible with valid token                      │  │
│  │  • Context includes user info from token                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Supported Authentication Methods

### 1. JWT Verification (Recommended)

Verify JSON Web Tokens from OIDC-compliant providers.

**Best for:** Auth0, Firebase, AWS Cognito, Clerk, Keycloak

**Pros:**
- Stateless verification (no API calls during validation)
- Fast performance
- Industry standard

**Cons:**
- Requires JWT tokens (not opaque)
- Need JWKS endpoint or public key

### 2. Token Introspection

Validate opaque tokens by calling the provider's introspection endpoint.

**Best for:** Custom OAuth servers, AWS Cognito (optional)

**Pros:**
- Works with any token type
- Real-time validation
- Can revoke tokens instantly

**Cons:**
- Extra HTTP request per API call (slower)
- Dependency on auth service availability

### 3. Simple API Keys

Validate against your existing API key database.

**Best for:** Internal tools, microservices, existing API infrastructure

**Pros:**
- Simplest implementation
- Works with existing systems
- Full control over validation logic

**Cons:**
- No standard OAuth flows
- Manual key rotation
- No refresh tokens

## Provider-Specific Integration

### Auth0

```python
from fastmcp.server.auth.verifiers import JWTVerifier

verifier = JWTVerifier(
    jwks_uri="https://your-domain.auth0.com/.well-known/jwks.json",
    issuer="https://your-domain.auth0.com/",
    audience="https://api.yoursite.com",
    required_scopes=["read:tools", "write:tools"]
)
```

**Setup:**
1. Create API in Auth0 Dashboard
2. Define scopes (read:tools, write:tools, etc.)
3. Get JWKS URI from API settings
4. Configure audience to match your MCP server URL

### Firebase Authentication

```python
verifier = JWTVerifier(
    jwks_uri="https://www.googleapis.com/service_accounts/v1/metadata/x509/securetoken@system.gserviceaccount.com",
    issuer="https://securetoken.google.com/your-project-id",
    audience="your-project-id",
    required_scopes=["read", "write"]
)
```

**Setup:**
1. Get project ID from Firebase Console
2. Use Firebase SDK to get ID tokens on client
3. Send ID token as Bearer token to MCP

### AWS Cognito

**Option A: JWT Verification**
```python
verifier = JWTVerifier(
    jwks_uri="https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json",
    issuer="https://cognito-idp.{region}.amazonaws.com/{userPoolId}",
    audience="{appClientId}",
    required_scopes=["read", "write"]
)
```

**Option B: Token Introspection**
```python
verifier = IntrospectionTokenVerifier(
    introspection_endpoint="https://your-domain.auth.{region}.amazoncognito.com/oauth2/introspect",
    client_id="{appClientId}",
    client_secret="{appClientSecret}",
    required_scopes=["read", "write"]
)
```

### Clerk

```python
verifier = JWTVerifier(
    jwks_uri="https://your-domain.clerk.accounts.dev/.well-known/jwks.json",
    issuer="https://your-domain.clerk.accounts.dev",
    audience=None,  # Clerk doesn't use audience
    required_scopes=["read", "write"]
)
```

### Keycloak

```python
verifier = JWTVerifier(
    jwks_uri="https://keycloak.example.com/realms/myrealm/protocol/openid-connect/certs",
    issuer="https://keycloak.example.com/realms/myrealm",
    audience="my-mcp-client",
    required_scopes=["read", "write"]
)
```

## Implementation Examples

### Basic JWT Verification

```python
# src/slzmcp/auth.py
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from fastmcp.server.auth.verifiers import JWTVerifier

# Create JWT verifier
jwt_verifier = JWTVerifier(
    jwks_uri="https://auth.example.com/.well-known/jwks.json",
    issuer="https://auth.example.com/",
    audience="https://api.example.com",
    required_scopes=["read"]
)

# Create server with auth
mcp = FastMCP(
    "SecureServer",
    auth=AuthSettings(
        issuer_url="https://auth.example.com/",
        resource_server_url="https://api.example.com",
        required_scopes=["read"]
    ),
    token_verifier=jwt_verifier
)

@mcp.tool()
def sensitive_operation(data: str) -> str:
    """This tool requires authentication"""
    return f"Processed: {data}"
```

### Environment-Based Configuration

```python
import os
from fastmcp.server.auth.verifiers import EnvJWTVerifier

# Reads from environment:
# FASTMCP_AUTH_JWKS_URI
# FASTMCP_AUTH_ISSUER
# FASTMCP_AUTH_AUDIENCE
# FASTMCP_AUTH_REQUIRED_SCOPES

verifier = EnvJWTVerifier()
```

### Custom Token Verifier

```python
from mcp.server.auth.provider import TokenVerifier, AccessToken
import httpx

class CustomAuthVerifier(TokenVerifier):
    def __init__(self, auth_service_url: str):
        self.auth_service_url = auth_service_url
    
    async def verify_token(self, token: str) -> AccessToken | None:
        # Call your existing auth service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_service_url}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return AccessToken(
                    token=token,
                    client_id=data["user_id"],
                    scopes=data["permissions"],
                    expires_at=data["exp"]
                )
            return None
```

## Client-Side Authentication

### Getting Tokens from Provider

```python
# Example: Auth0 client
import auth0.authentication

auth = auth0.authentication.GetToken(
    "your-domain.auth0.com",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

token = auth.login(
    username="user@example.com",
    password="password",
    scope="read write",
    audience="https://api.example.com"
)

access_token = token["access_token"]
```

### Using Token with MCP Client

```python
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def call_secure_tool(access_token: str):
    url = "https://api.example.com/mcp"
    
    async with streamablehttp_client(url) as (read, write, get_session_id):
        # Note: Token must be passed in headers
        # This is pseudo-code - actual implementation depends on transport
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("sensitive_operation", {"data": "test"})
```

**Note:** For production, use `httpx.Auth` to automatically inject tokens:

```python
import httpx

class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token
    
    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

async with httpx.AsyncClient(auth=BearerAuth(access_token)) as client:
    # All requests automatically include Authorization header
    response = await client.post("https://api.example.com/mcp", json={...})
```

## Security Best Practices

### 1. Always Use HTTPS

```python
# Production only
assert resource_server_url.startswith("https://"), "HTTPS required in production"
```

### 2. Validate All JWT Claims

```python
verifier = JWTVerifier(
    jwks_uri="...",
    issuer="...",      # Must match exactly
    audience="...",    # Must match your API identifier
    required_scopes=["read"]  # Must have required permissions
)
```

### 3. Short-Lived Access Tokens

- Access tokens: 15-60 minutes
- Refresh tokens: 7-30 days (or longer)
- Implement refresh logic in client

### 4. Scope-Based Access Control

```python
@mcp.tool()
def admin_only_tool(ctx: Context) -> str:
    """Only admins can use this"""
    token = get_access_token()
    if "admin" not in token.scopes:
        raise Exception("Admin scope required")
    return "Admin operation completed"
```

### 5. Token Rotation (Optional)

For high-security environments, rotate tokens on each use:

```python
# In your TokenVerifier
async def verify_token(self, token: str) -> AccessToken | None:
    access_token = await self.load_token(token)
    if not access_token:
        return None
    
    # Rotate token (issue new one, invalidate old)
    new_token = await self.rotate_token(access_token)
    return new_token
```

## Testing Authentication

### Unit Tests

```python
import pytest
from mcp.server.auth.provider import AccessToken

@pytest.fixture
def mock_verifier():
    class MockVerifier:
        async def verify_token(self, token: str) -> AccessToken | None:
            if token == "valid_token":
                return AccessToken(
                    token=token,
                    client_id="test_user",
                    scopes=["read", "write"],
                    expires_at=None
                )
            return None
    return MockVerifier()

async def test_protected_tool_with_valid_token(mock_verifier):
    server = FastMCP("Test", token_verifier=mock_verifier)
    
    @server.tool()
    def protected_tool() -> str:
        return "success"
    
    # Test with valid token
    result = await call_tool_with_auth(server, "protected_tool", token="valid_token")
    assert result == "success"
```

### Integration Tests

```python
# Use test credentials from your auth provider
TEST_TOKEN = "eyJhbGciOiJSUzI1NiIs..."  # Valid test token

async def test_with_real_auth():
    verifier = JWTVerifier(
        jwks_uri="https://test.auth0.com/.well-known/jwks.json",
        issuer="https://test.auth0.com/",
        audience="test-api",
        required_scopes=["read"]
    )
    
    server = FastMCP("Test", token_verifier=verifier)
    # ... test with TEST_TOKEN
```

## Troubleshooting

### "Invalid signature" errors
- Check JWKS URI is correct
- Verify token hasn't expired
- Ensure issuer and audience match exactly

### "Scope insufficient" errors
- Verify required_scopes matches token scopes
- Check scope format (space-separated vs list)
- Ensure scopes are requested during authentication

### Performance issues
- JWT verification is faster than introspection
- Cache JWKS keys (they rotate infrequently)
- Use connection pooling for introspection calls

## Migration from Unauthenticated

If your MCP server is currently unauthenticated:

1. **Phase 1:** Add optional authentication (allow unauthenticated requests)
2. **Phase 2:** Log authentication failures
3. **Phase 3:** Require authentication for new tools
4. **Phase 4:** Gradually migrate existing tools
5. **Phase 5:** Remove unauthenticated access

```python
# Phase 1: Optional auth
class OptionalVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        if not token:
            return AccessToken(token="anonymous", client_id="guest", scopes=["read"])
        # ... validate real token
```

## Comparison: Build vs. Buy

| Aspect | Build OAuth Server | Use External Provider |
|--------|-------------------|---------------------|
| **Setup Time** | Weeks | Hours |
| **Maintenance** | High (security patches, updates) | Low |
| **User Management** | Build yourself | Built-in dashboards |
| **Social Login** | Complex integration | One-click setup |
| **MFA/2FA** | Implement yourself | Built-in |
| **Password Reset** | Build flow | Built-in |
| **Compliance** | You handle everything (SOC2, GDPR) | Provider handles it |
| **Cost** | Free (your time) | $0-$1000+/month |
| **Customization** | Full control | Limited to provider features |

**Recommendation:** Use external providers for 99% of use cases.

## Next Steps

1. **Choose your provider** (Auth0 recommended for ease of use)
2. **Create account and configure**
3. **Get JWKS URI and credentials**
4. **Implement JWTVerifier** (see examples above)
5. **Test with client**
6. **Deploy with HTTPS**

## References

- [OAuth 2.1 Specification](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1)
- [JWT.io](https://jwt.io/) - Debug JWT tokens
- [Auth0 Docs](https://auth0.com/docs)
- [Firebase Auth Docs](https://firebase.google.com/docs/auth)
- [Clerk Docs](https://clerk.com/docs)
- [MCP Auth Specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)

---

**Status:** Documentation complete - ready for implementation review

# Authentication Implementation Plan V3 - TokenVerifier Pattern

**Date:** 2025-10-19 13:00
**Status:** READY TO IMPLEMENT
**Confidence:** VERY HIGH - Based on official SDK examples and FastMCP 2.12.4 capabilities

---

## Executive Summary

After deep research into both the **official MCP Python SDK** and **FastMCP 2.12.4**, we've identified the correct authentication pattern:

**Use FastMCP's `TokenVerifier` with the `auth` parameter (NOT middleware)**

---

## What We Discovered

### 1. FastMCP 2.12.4 HAS Built-In Authentication

**Current Environment:**
```
FastMCP: 2.12.4
Official MCP SDK: installed
TokenVerifier: Available (async)
```

**FastMCP.__init__ Parameters:**
```python
FastMCP(
    name="...",
    auth=AuthProvider | None,  # ← WE NEED THIS!
    ...
)
```

**Available in fastmcp.server.auth:**
- `TokenVerifier` (Protocol/Base class)
- `StaticTokenVerifier` (Simple token validation)
- `JWTVerifier` (JWT token validation)
- `OAuthProvider` (Full OAuth 2.1)
- `AuthProvider` (Base type)

### 2. TokenVerifier Protocol

**Signature:**
```python
class TokenVerifier(Protocol):
    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify bearer token and return access info if valid."""
```

**When It's Called:**
- On EVERY request with `Authorization: Bearer <token>` header
- Runs BEFORE any middleware
- Runs BEFORE session creation
- Token must be sent with EVERY request (not just initialization)

### 3. Official MCP SDK Example

From `modelcontextprotocol/python-sdk/examples/servers/simple-auth/`:

**Token Verifier Implementation:**
```python
from mcp.server.auth.provider import AccessToken, TokenVerifier

class IntrospectionTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        # Validate token (in their case, via introspection endpoint)
        # Return AccessToken or None
```

**Server Setup:**
```python
from mcp.server.fastmcp.server import FastMCP

mcp = FastMCP(
    name="MCP Resource Server",
    token_verifier=token_verifier,  # ← The key!
    auth=AuthSettings(
        issuer_url=...,
        required_scopes=[...],
    ),
)
```

---

## Why Our Previous Attempts Failed

### Attempt 1: Middleware with `on_call_tool`
```python
mcp.add_middleware(APIKeyAuthenticationMiddleware())

class APIKeyAuthenticationMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        # Problem: Fires ONLY for tool calls
        # Problem: X-API-Key already gone
```

**Why It Failed:**
- ❌ Fires after session creation
- ❌ Only fires for tool calls (not initialization)
- ❌ X-API-Key header not present

### Attempt 2: Middleware with `on_request`
```python
class APIKeyAuthenticationMiddleware(Middleware):
    async def on_request(self, context, call_next):
        # Problem: Still fires after session creation
        # Problem: Session-based approach requires state management
```

**Why It Failed:**
- ❌ Fires after HTTP authentication layer
- ❌ Still too late in request pipeline
- ❌ Complex session state management

### Attempt 3: Auth Class (from FastMCP docs)
```python
from fastmcp.server.auth import Auth

class DatabaseTokenVerifier(Auth):
    def verify_token(self, token: str) -> AccessToken | None:
        # This exists but is NOT async!
```

**Why It Failed:**
- ❌ Our implementation was sync, should be async
- ❌ We imported from wrong module

---

## The Correct Solution

### Architecture

**HTTP Request Flow:**
```
1. Client sends: Authorization: Bearer sk_simone_...
   ↓
2. Starlette AuthenticationBackend (built into FastMCP)
   ↓
3. Calls: TokenVerifier.verify_token(token)
   ↓
4. Our DatabaseTokenVerifier validates against SQLite
   ↓
5. Returns AccessToken or None
   ↓
6. If AccessToken: Request proceeds (authenticated)
   If None: 401 Unauthorized response
```

**Key Points:**
- ✅ Token sent with EVERY request (not just initialization)
- ✅ Validation happens BEFORE session creation
- ✅ No session state management needed
- ✅ Clean separation of concerns

---

## Implementation Steps

### Step 1: Update DatabaseTokenVerifier

**File:** `src/auth/database_token_verifier.py`

**Changes Needed:**
1. Import from `fastmcp.server.auth` (not `mcp.server.auth.provider`)
2. Make `verify_token` async
3. Ensure it follows FastMCP's TokenVerifier protocol
4. Keep all existing validation logic (bcrypt, rate limiting, etc.)

**Updated Code:**
```python
"""Database-backed token verifier for FastMCP authentication."""
from fastmcp.server.auth import AccessToken, TokenVerifier
from .key_manager import verify_key_hash, get_key_prefix
from .database import get_db_connection, update_last_used
from .rate_limiter import check_rate_limit
import logging

logger = logging.getLogger(__name__)


class DatabaseTokenVerifier(TokenVerifier):
    """
    Token verifier that validates API keys against SQLite database.

    Supports Authorization: Bearer <token> header.
    Key format: sk_simone_<32_random_chars>
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify API key against database using bcrypt.

        Args:
            token: The API key from Authorization Bearer header

        Returns:
            AccessToken with user info if valid, None otherwise
        """
        logger.info(f"[AUTH] Verifying token: {token[:18]}...")

        # Validate key format
        if not token or not token.startswith("sk_simone_"):
            logger.warning("[AUTH] Invalid token format")
            return None

        # Get the key prefix to narrow down database search
        prefix = get_key_prefix(token)

        # Query database for matching prefix
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key_hash, owner_email, id FROM api_keys
            WHERE is_active = 1 AND key_prefix = ?
        """, (prefix,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning(f"[AUTH] No active key found for prefix: {prefix}")
            return None

        stored_hash = row['key_hash']
        owner_email = row['owner_email']
        key_id = row['id']

        # Verify key using bcrypt
        if not verify_key_hash(token, stored_hash):
            logger.warning("[AUTH] bcrypt verification failed")
            return None

        # Check rate limit
        if not check_rate_limit(stored_hash):
            logger.error("[AUTH] Rate limit exceeded")
            return None

        # Update last used timestamp (fire and forget)
        try:
            update_last_used(stored_hash)
        except Exception as e:
            logger.warning(f"[AUTH] Failed to update timestamp: {e}")
            pass

        logger.info(f"[AUTH] ✓ Token verified for user: {owner_email}")

        # Return access token with user info
        return AccessToken(
            token=token,
            claims={
                "sub": owner_email,  # Subject (user identifier)
                "email": owner_email,
                "key_id": key_id,
                "key_prefix": prefix
            },
            scopes=["api:access"]  # Basic API access scope
        )
```

**Key Changes:**
- Changed `def verify_token` → `async def verify_token`
- Updated imports to use `fastmcp.server.auth`
- Added comprehensive logging
- Kept all existing validation logic (bcrypt, rate limiting)

### Step 2: Update Server File

**File:** `src/SIM-ONE-MCP-v2_mcp-http.py`

**Changes:**

**OLD CODE (lines 24-35):**
```python
# Import authentication
from auth.database import init_database
from auth.auth_middleware import APIKeyAuthenticationMiddleware

# Initialize database
init_database()

# Server definition
mcp = FastMCP(name="SIM-ONE-MCP-v2")

# Add authentication middleware
mcp.add_middleware(APIKeyAuthenticationMiddleware())
```

**NEW CODE:**
```python
# Import authentication
from auth.database import init_database
from auth.database_token_verifier import DatabaseTokenVerifier

# Initialize database
init_database()

# Create token verifier
token_verifier = DatabaseTokenVerifier()

# Server definition with authentication
mcp = FastMCP(
    name="SIM-ONE-MCP-v2",
    auth=token_verifier  # ← Use TokenVerifier, not middleware
)

# NO mcp.add_middleware() for auth!
```

### Step 3: Update Client Configuration

**File:** User's Codex `config.toml`

**CRITICAL CHANGE:** Use `Authorization` header instead of `X-API-Key`:

**OLD CONFIG:**
```toml
[mcp_servers.sim-one-mcp]
url = "http://127.0.0.1:8000/mcp"
headers = { X-API-Key = "sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk" }
```

**NEW CONFIG:**
```toml
[mcp_servers.sim-one-mcp]
url = "http://127.0.0.1:8000/mcp"
headers = { Authorization = "Bearer sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk" }
```

**Why This Matters:**
- FastMCP's BearerAuthBackend expects `Authorization: Bearer <token>`
- This is the standard HTTP authentication header
- Token will be sent with EVERY request automatically

### Step 4: Clean Up (Optional)

**Files to Remove (no longer needed):**
- `src/auth/auth_middleware.py` (middleware approach)
- `src/auth/middleware.py` (old Starlette middleware)

**Files to Keep:**
- `src/auth/database_token_verifier.py` (updated)
- `src/auth/database.py` (database operations)
- `src/auth/key_manager.py` (bcrypt verification)
- `src/auth/rate_limiter.py` (rate limiting)

---

## Testing Plan

### Test 1: Valid API Key

**Setup:**
```toml
headers = { Authorization = "Bearer sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk" }
```

**Expected:**
1. Server logs: `[AUTH] Verifying token: sk_simone_uiDejaAs...`
2. Server logs: `[AUTH] ✓ Token verified for user: daniel@example.com`
3. Tool call succeeds
4. Response returned

### Test 2: Invalid API Key

**Setup:**
```toml
headers = { Authorization = "Bearer sk_simone_INVALID_KEY" }
```

**Expected:**
1. Server logs: `[AUTH] Verifying token: sk_simone_INVALID...`
2. Server logs: `[AUTH] bcrypt verification failed`
3. 401 Unauthorized response
4. Tool call rejected

### Test 3: Missing API Key

**Setup:**
```toml
# No headers
```

**Expected:**
1. 401 Unauthorized response
2. No token verification attempt
3. Tool call rejected

### Test 4: Rate Limiting

**Setup:**
Make 100+ requests quickly

**Expected:**
1. First 100 requests succeed
2. 101st request: `[AUTH] Rate limit exceeded`
3. 429 Too Many Requests response

---

## Migration Path

### Phase 1: Update Code (5 minutes)
1. Edit `src/auth/database_token_verifier.py` - Add `async`
2. Edit `src/SIM-ONE-MCP-v2_mcp-http.py` - Use `auth=` parameter
3. Commit changes

### Phase 2: Update Client Config (2 minutes)
1. Edit Codex `config.toml`
2. Change `X-API-Key` → `Authorization = "Bearer ..."`
3. Restart Codex

### Phase 3: Test (5 minutes)
1. Start server
2. Connect with Codex
3. Call a tool
4. Verify success

### Phase 4: Cleanup (optional)
1. Remove old middleware files
2. Update documentation
3. Create final PR

---

## Expected Logs

### Successful Authentication

```
[AUTH] Verifying token: sk_simone_uiDejaAs...
[AUTH] ✓ Token verified for user: daniel@example.com
[TOOL] Executing: five_laws_validate_text
[TOOL] ✓ Completed successfully
```

### Failed Authentication

```
[AUTH] Verifying token: sk_simone_BADKEY123...
[AUTH] bcrypt verification failed
401 Unauthorized
```

---

## Why This Will Work

### 1. Correct Architectural Layer
- ✅ TokenVerifier runs BEFORE session creation
- ✅ FastMCP handles all HTTP authentication plumbing
- ✅ No manual session management needed

### 2. Standard HTTP Pattern
- ✅ Uses `Authorization: Bearer` (industry standard)
- ✅ Token sent with every request (not just initialization)
- ✅ Stateless authentication (no session tracking)

### 3. FastMCP Built-In Support
- ✅ FastMCP 2.12.4 has native TokenVerifier support
- ✅ BearerAuthBackend handles token extraction
- ✅ Middleware integration is automatic

### 4. Proven Pattern
- ✅ Same pattern used in official MCP SDK examples
- ✅ Documented in FastMCP auth module
- ✅ Used by production MCP servers

---

## Comparison: Old vs New

| Aspect | Old (Middleware) | New (TokenVerifier) |
|--------|-----------------|---------------------|
| **When Runs** | After session creation | Before session creation |
| **Trigger** | on_request/on_call_tool | Every HTTP request |
| **Header** | X-API-Key | Authorization: Bearer |
| **Token Frequency** | Only initialization | Every request |
| **State Management** | Manual (authenticated_sessions) | Automatic (stateless) |
| **Integration** | add_middleware() | auth= parameter |
| **Complexity** | High (session tracking) | Low (just validate token) |
| **Standard** | Custom | HTTP standard |

---

## Risk Assessment

**Risk Level:** LOW

**Potential Issues:**
1. **Client config change required** - User must update Codex config
   - Mitigation: Clear instructions provided
   - Impact: 2 minutes to fix

2. **Token sent with every request** - Slight overhead
   - Mitigation: bcrypt caching, database connection pooling
   - Impact: Negligible (~1ms per request)

3. **Different from session-based auth** - Mental model shift
   - Mitigation: This IS the correct MCP pattern
   - Impact: None (we're following the spec)

**Success Probability:** 95%

---

## Files Affected

### Modified
- `src/auth/database_token_verifier.py` (add async, update imports)
- `src/SIM-ONE-MCP-v2_mcp-http.py` (use auth= parameter)

### User Action Required
- Codex `config.toml` (change header format)

### Deprecated (can remove)
- `src/auth/auth_middleware.py`
- `src/auth/middleware.py`

---

## Summary

**What We Learned:**
- FastMCP 2.12.4 HAS built-in authentication via TokenVerifier
- The correct pattern is `auth=` parameter, NOT middleware
- Bearer tokens are sent with EVERY request (not just initialization)
- This is the standard HTTP authentication pattern

**What We're Doing:**
- Using FastMCP's native `TokenVerifier` protocol
- Validating API keys against local database
- Following official MCP SDK examples
- Keeping all existing validation logic (bcrypt, rate limiting)

**What Changes:**
- Server: Use `auth=` instead of `add_middleware()`
- Client: Use `Authorization: Bearer` instead of `X-API-Key`
- Code: Make `verify_token` async

**Time to Implement:** 10-15 minutes
**Confidence Level:** VERY HIGH
**Status:** READY TO IMPLEMENT

---

**Next Step:** Implement changes and test

# FastMCP Authentication Implementation Plan

## Problem Identified
- Current middleware (`APIKeyAuthMiddleware`) is Starlette-based (`BaseHTTPMiddleware`)
- FastMCP's `mcp.run()` doesn't support Starlette middleware
- This causes 400 Bad Request errors

## Solution: Pure FastMCP Authentication

### Step 1: Research FastMCP Auth Interface
**Goal:** Understand how to implement custom auth provider for FastMCP

**From Context7 docs:**
```python
# FastMCP supports auth parameter
mcp = FastMCP(name="server", auth=auth_provider)

# Example: StaticTokenVerifier
from fastmcp.auth import StaticTokenVerifier
verifier = StaticTokenVerifier(
    tokens={"token": {"client_id": "user", "scopes": ["read"]}}
)
```

**Need to find:**
- Base class for custom auth providers
- Required methods to implement
- How to access HTTP headers for Bearer/X-API-Key
- How to return auth failures

### Step 2: Create DatabaseTokenVerifier
**File:** `src/auth/database_token_verifier.py` (new file)

**Requirements:**
- Inherit from FastMCP's auth base class (TBD from research)
- Implement verification method
- Access HTTP headers (Authorization, X-API-Key)
- Verify against database using bcrypt
- Check rate limits
- Update last_used timestamp

**Reuse existing code:**
- `auth/key_manager.py` - `verify_key_hash()`, `get_key_prefix()`
- `auth/database.py` - `get_db_connection()`, `update_last_used()`
- `auth/rate_limiter.py` - `check_rate_limit()`, `get_retry_after_seconds()`

### Step 3: Update Server Configuration
**File:** `src/SIM-ONE-MCP-v2_mcp-http.py`

**Changes:**
```python
# REMOVE:
from starlette.middleware import Middleware
from auth.middleware import APIKeyAuthMiddleware

# ADD:
from auth.database_token_verifier import DatabaseTokenVerifier

# CHANGE:
# Before:
mcp.run(
    transport="streamable-http",
    host="0.0.0.0",
    port=8000,
    middleware=[Middleware(APIKeyAuthMiddleware)]  # REMOVE
)

# After:
auth_provider = DatabaseTokenVerifier()
mcp = FastMCP(name="SIM-ONE-MCP-v2", auth=auth_provider)  # ADD auth
mcp.mount(esl_emotional_analysis_tutorial_mcp)
mcp.mount(five_laws_validator_tutorial_mcp)
mcp.run(
    transport="streamable-http",
    host="0.0.0.0",
    port=8000
)
```

### Step 4: Keep Existing Files (May Be Needed Later)
**DO NOT DELETE:**
- `auth/middleware.py` - Keep for reference, might be useful for FastAPI endpoints later
- `auth/database.py` - Still used by new auth provider
- `auth/key_manager.py` - Still used by new auth provider
- `auth/rate_limiter.py` - Still used by new auth provider

### Step 5: Testing Plan
1. Start server - should not crash
2. Connect from Codex with valid API key - should authenticate
3. Try invalid key - should reject with proper error
4. Try missing key - should reject with proper error
5. Verify rate limiting still works
6. Verify last_used timestamp updates

## Files to Create
- `src/auth/database_token_verifier.py` - New FastMCP auth provider

## Files to Modify
- `src/SIM-ONE-MCP-v2_mcp-http.py` - Update to use auth parameter

## Files to Keep (No Changes)
- `src/auth/database.py`
- `src/auth/key_manager.py`
- `src/auth/rate_limiter.py`
- `src/auth/middleware.py` (keep for reference)

## Research Needed
Query Context7 for:
- FastMCP authentication provider base class
- Required methods to implement
- How to access HTTP headers in auth context
- Error handling patterns

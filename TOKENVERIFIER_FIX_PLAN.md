# TokenVerifier Fix Plan - V5 (CORRECT APPROACH)

**Date**: 2025-10-19 20:30
**Status**: READY FOR IMPLEMENTATION
**Confidence**: HIGH - Based on PR#3 CodeRabbit + Codex bot analysis

---

## What I Did Wrong

### Previous Attempt (database_token_verifier.py)

**4 Critical Mistakes:**

1. **Line 4**: `from fastmcp.server.auth import AccessToken, Auth`
   - Imported `Auth` instead of `TokenVerifier`

2. **Line 10**: `class DatabaseTokenVerifier(Auth):`
   - Extended `Auth` instead of `TokenVerifier`
   - This triggered OAuth discovery because FastMCP expected full OAuth

3. **Line 22**: `def verify_token(self, token: str) -> AccessToken | None:`
   - NOT async - should be `async def verify_token`
   - Protocol requires async

4. **Line 48**: `row = cursor.fetchone()`
   - Should use `fetchall()` to handle duplicate key_prefix values

**Why It Failed:**
- FastMCP saw `Auth` base class and expected OAuth 2.1 infrastructure
- Triggered OAuth discovery endpoints
- I assumed TokenVerifier approach was wrong
- Switched to middleware (which also doesn't work)

---

## The Correct Solution (From Bots)

### CodeRabbit's Analysis

> "The middleware approach cannot work because FastMCP middleware hooks execute after HTTP transport initialization, when custom headers are no longer available."

> "The TokenVerifier approach (see AUTHENTICATION_IMPLEMENTATION_PLAN_V3.md) solves this by running at the HTTP layer before headers are consumed."

### Request Flow

```
HTTP Request
    ↓
[1] Starlette AuthenticationBackend ← TokenVerifier runs HERE
    ↓
[2] Session Creation
    ↓
[3] Middleware (on_request) ← We were trying to auth HERE (too late!)
    ↓
[4] Tool Execution
```

**Middleware runs at layer [3]** - headers already consumed
**TokenVerifier runs at layer [1]** - headers available

---

## Implementation Steps

### Step 1: Fix database_token_verifier.py

**File**: `src/auth/database_token_verifier.py`

**Change 1** (Line 4):
```python
# WRONG
from fastmcp.server.auth import AccessToken, Auth

# CORRECT
from fastmcp.server.auth import AccessToken, TokenVerifier
```

**Change 2** (Line 10):
```python
# WRONG
class DatabaseTokenVerifier(Auth):

# CORRECT
class DatabaseTokenVerifier(TokenVerifier):
```

**Change 3** (Line 22):
```python
# WRONG
def verify_token(self, token: str) -> AccessToken | None:

# CORRECT
async def verify_token(self, token: str) -> AccessToken | None:
```

**Change 4** (Lines 40-60): Fix database leak and fetchone() bug
```python
# Query database
conn = get_db_connection()

try:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT key_hash, user_email, id FROM api_keys
        WHERE is_active = 1 AND key_prefix = ?
    """, (prefix,))

    rows = cursor.fetchall()  # Get ALL matching rows
finally:
    conn.close()  # Always close

if not rows:
    return None

# Try each candidate with bcrypt
for row in rows:
    stored_hash = row['key_hash']

    if verify_key_hash(token, stored_hash):
        user_email = row['user_email']
        key_id = row['id']

        # Check rate limit
        if not check_rate_limit(stored_hash):
            return None

        # Update last used
        try:
            update_last_used(stored_hash)
        except Exception:
            pass

        # Return access token
        return AccessToken(
            token=token,
            claims={
                "sub": user_email,
                "email": user_email,
                "key_id": key_id,
                "key_prefix": prefix
            },
            scopes=["api:access"]
        )

# No valid key found
return None
```

### Step 2: Fix Server Setup

**File**: `src/SIM-ONE-MCP-v2_mcp-http.py`

**WRONG (Current)**:
```python
from auth.auth_middleware import APIKeyAuthenticationMiddleware

mcp = FastMCP(name="SIM-ONE-MCP-v2")
mcp.add_middleware(APIKeyAuthenticationMiddleware())
```

**CORRECT (Needed)**:
```python
from auth.database_token_verifier import DatabaseTokenVerifier

mcp = FastMCP(
    name="SIM-ONE-MCP-v2",
    auth=DatabaseTokenVerifier()  # ← Use auth= parameter
)
```

### Step 3: Client Config (Already Correct)

User already updated Codex config:
```toml
[mcp_servers.sim-one-mcp]
url = "http://127.0.0.1:8000/mcp"
headers = { Authorization = "Bearer sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk" }
```

This is correct for TokenVerifier approach.

---

## Testing Plan

### Test 1: Server Starts Without OAuth Errors
```bash
uv run --python "C:\Users\admin\OneDrive\Desktop\Paper2Agent\sim-one-venv\Scripts\python.exe" --with fastmcp "C:\Claude\SIM-ONE-MCP-v2\src\SIM-ONE-MCP-v2_mcp-http.py"
```

**Expected**:
- Server starts on port 8000
- NO OAuth discovery endpoint errors
- No "/.well-known/oauth-authorization-server" requests

### Test 2: Connect with Codex
**Expected**:
- Tools discovered successfully
- No "Unsupported" auth status
- Tools list shows all available tools

### Test 3: Call a Tool
```
Call: esl_analyze_emotion with text "I am happy"
```

**Expected**:
- Server logs show TokenVerifier.verify_token() called
- API key validated against database
- Tool executes successfully
- Returns emotional analysis result

### Test 4: Invalid API Key
Update Codex config with wrong key

**Expected**:
- Connection rejected
- 401 Unauthorized
- No tools discovered

---

## Why This Will Work

### 1. Correct Base Class
`TokenVerifier` is a Protocol that FastMCP expects for the `auth=` parameter. It won't trigger OAuth discovery.

### 2. Async Protocol
`async def verify_token()` matches the protocol signature. FastMCP can await it properly.

### 3. Runs at HTTP Layer
TokenVerifier is called by Starlette's AuthenticationMiddleware BEFORE MCP session creation, when Authorization headers are still present.

### 4. Standard Pattern
This is the official MCP SDK pattern, documented in `examples/servers/simple-auth/`.

---

## Bot Comment Summary

### CodeRabbit (6 comments on PR#3):

1. **V4 plan contradicts research findings** - middleware is wrong, TokenVerifier is correct
2. **Research doc says use TokenVerifier** - but implementation uses middleware
3. **TODO tracks wrong approach** - should track V3 (TokenVerifier) not V4 (middleware)
4. **Session cache is unreachable code** - first request always fails, session never created
5. **Architectural flaw confirmed** - middleware runs after headers consumed
6. **Security issue** - API key exposed in TODO file

### Codex Bot (1 comment on PR#3):

1. **P1: Session cache bypasses revocation** - cached sessions never re-validated, rate limits not applied

---

## Success Criteria

- [ ] No OAuth discovery errors
- [ ] Tools discovered in Codex
- [ ] Tool calls work
- [ ] Invalid keys rejected
- [ ] Database connections properly closed
- [ ] Multiple keys with same prefix handled correctly
- [ ] Rate limiting works on every request
- [ ] Key revocation takes effect immediately

---

## References

- **PR#3**: https://github.com/dansasser/SIM-ONE-MCP-V2/pull/3
- **CodeRabbit Comments**: 6 critical findings
- **Official MCP SDK**: modelcontextprotocol/python-sdk/examples/servers/simple-auth/
- **FastMCP Source**: BearerAuthBackend implementation

---

## Confidence Level

**VERY HIGH** - This fixes the exact 4 mistakes I made:
1. Wrong import (Auth vs TokenVerifier)
2. Wrong base class (Auth vs TokenVerifier)
3. Missing async
4. fetchone() bug

All logic is correct, just need to fix the implementation details.

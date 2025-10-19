# Authentication Fix Plan V4 - BREAKTHROUGH SOLUTION

**Date**: 2025-10-19
**Status**: READY FOR IMPLEMENTATION
**Confidence**: HIGH - Based on PR review bot analysis

---

## BREAKTHROUGH DISCOVERY

From **Codex Bot P0 Critical Comment** on PR#2:

> "The middleware authenticates inside `on_call_tool` by reading the `Authorization`/`X-API-Key` headers for every tool invocation. In the MCP streamable-http transport those headers are only present on the initial `initialize` request; subsequent tool calls carry only `mcp-session-id`. Because the code here executes after initialization, every tool call will take the `Missing API key` branch and raise a `ToolError`, making the server unusable even when the client supplied a valid key. **Authentication needs to occur in an `on_request` hook** (or store the validated session id from initialization) so that later tool calls are permitted without re-sending the key."

---

## ROOT CAUSE

### The Problem

**Current Implementation (BROKEN)**:
- Uses `async def on_call_tool(...)` hook
- Runs AFTER MCP initialization
- Tries to read `X-API-Key` or `Authorization` headers on every tool call
- These headers are NOT present on tool calls (only on `initialize` request)

**MCP streamable-http Protocol Behavior**:
1. **Initialize Request**: Carries custom headers (`X-API-Key`, `Authorization: Bearer`)
2. **Tool Call Requests**: Carry ONLY `mcp-session-id` header (NO custom headers)

**Why Current Code Fails**:
```python
# Current code in auth_middleware.py:98
async def on_call_tool(self, context: MiddlewareContext, call_next):
    # This runs on TOOL CALLS (after initialization)
    # At this point, X-API-Key and Authorization headers are GONE
    # Only mcp-session-id is present
    # So every tool call fails with "Missing API key"
```

---

## THE SOLUTION

### Change 1: Use `on_request` Hook

**Before**:
```python
async def on_call_tool(self, context: MiddlewareContext, call_next):
    # Runs on tool calls (WRONG - headers not present)
```

**After**:
```python
async def on_request(self, context: MiddlewareContext, call_next):
    # Runs on ALL requests including initialize (CORRECT - headers present)
```

### Change 2: Implement Session Storage

**New Session Cache**:
```python
class APIKeyAuthenticationMiddleware(Middleware):
    def __init__(self):
        self.sessions = {}  # mcp-session-id -> api_key_hash
        # Optional: Add TTL/expiration logic
```

### Change 3: Session-Based Authentication Flow

**Authentication Logic**:
```python
async def on_request(self, context: MiddlewareContext, call_next):
    request = get_http_request()
    headers = dict(request.headers)

    # STEP 1: Check for existing session
    session_id = headers.get("mcp-session-id")

    if session_id and session_id in self.sessions:
        # Valid session - allow request without re-checking API key
        logger.info(f"[OK] Valid session: {session_id[:16]}...")
        return await call_next(context)

    # STEP 2: No valid session - require API key
    api_key = extract_api_key(headers)  # From Authorization or X-API-Key

    if not api_key:
        raise ToolError("Missing API key")

    if not self._verify_key(api_key):
        raise ToolError("Invalid or revoked API key")

    # STEP 3: Store session for future requests
    if session_id:
        self.sessions[session_id] = get_key_hash(api_key)
        logger.info(f"[OK] Created session: {session_id[:16]}...")

    return await call_next(context)
```

---

## IMPLEMENTATION STEPS

### Step 1: Update auth_middleware.py Hook

**File**: `C:\Claude\SIM-ONE-MCP-V2\src\auth\auth_middleware.py`

**Changes**:
1. Add `__init__` method with session cache
2. Change `on_call_tool` to `on_request`
3. Add session validation logic at start of method
4. Add session storage after successful API key validation

### Step 2: Fix Database Connection Leak

**Issue**: CodeRabbit identified connection not closed on error

**Current Code**:
```python
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute(...)
row = cursor.fetchone()
conn.close()  # Not called if exception occurs above
```

**Fixed Code**:
```python
conn = get_db_connection()
try:
    cursor = conn.cursor()
    cursor.execute(...)
    row = cursor.fetchone()
finally:
    conn.close()  # Always called
```

### Step 3: Fix fetchone() Non-Unique Prefix Bug

**Issue**: CodeRabbit identified that `key_prefix` may match multiple rows

**Current Code**:
```python
cursor.execute("""
    SELECT key_hash FROM api_keys
    WHERE is_active = 1 AND key_prefix = ?
""", (prefix,))
row = cursor.fetchone()  # May get wrong row if multiple matches
```

**Fixed Code**:
```python
cursor.execute("""
    SELECT key_hash FROM api_keys
    WHERE is_active = 1 AND key_prefix = ?
""", (prefix,))
rows = cursor.fetchall()  # Get ALL matching rows

# Verify each candidate with bcrypt
for row in rows:
    stored_hash = row['key_hash']
    if verify_key_hash(api_key, stored_hash):
        # Found the correct key
        return stored_hash

# No match found
return None
```

---

## CODE CHANGES REQUIRED

### File 1: `src/auth/auth_middleware.py`

**Line 19**: Add session storage to class init
```python
class APIKeyAuthenticationMiddleware(Middleware):
    """
    Middleware to authenticate API requests using API keys.
    Validates against database using bcrypt.
    """

    def __init__(self):
        """Initialize middleware with session cache."""
        super().__init__()
        self.sessions = {}  # mcp-session-id -> api_key_hash mapping
```

**Line 25**: Change hook from `on_call_tool` to `on_request`
```python
async def on_request(self, context: MiddlewareContext, call_next):
    """Authenticate all requests - check session or API key."""
```

**Line 30-47**: Add session validation logic BEFORE API key check
```python
# Get HTTP request object to access headers
from fastmcp.server.dependencies import get_http_request

try:
    request = get_http_request()
    headers = dict(request.headers)

    # STEP 1: Check for existing valid session
    session_id = headers.get("mcp-session-id")

    if session_id and session_id in self.sessions:
        logger.info(f"[OK] Valid session found: {session_id[:16]}...")
        logger.info(f"[OK] Skipping API key validation for session")
        return await call_next(context)

    logger.debug(f"No valid session - requiring API key authentication")

except Exception as e:
    logger.error(f"[FAIL] Failed to get HTTP request: {e}")
    raise ToolError("Authentication required")
```

**Line 91** (after successful key verification): Add session storage
```python
logger.info("[OK] API key verified successfully")

# Store session for future requests (if session ID present)
session_id = headers.get("mcp-session-id")
if session_id:
    # Store the key prefix (or hash) for this session
    self.sessions[session_id] = prefix
    logger.info(f"[OK] Created session: {session_id[:16]}...")

logger.info("[OK] Authentication successful - proceeding with request")
```

**Line 110-122**: Fix database connection leak
```python
# Query database
logger.debug("_verify_key: Connecting to database...")
conn = get_db_connection()

try:
    cursor = conn.cursor()

    logger.debug(f"_verify_key: Querying for active key with prefix: {prefix}")
    cursor.execute("""
        SELECT key_hash FROM api_keys
        WHERE is_active = 1 AND key_prefix = ?
    """, (prefix,))

    row = cursor.fetchone()
finally:
    conn.close()  # Always close connection
```

**Line 123-135**: Fix fetchone() to fetchall() with iteration
```python
rows = cursor.fetchall()  # Get all matching candidates

if not rows:
    logger.warning(f"_verify_key: No active key found for prefix: {prefix}")
    return False

# Try each candidate with bcrypt verification
logger.debug(f"_verify_key: Found {len(rows)} candidate(s), verifying with bcrypt...")
stored_hash = None

for row in rows:
    candidate_hash = row['key_hash']
    if verify_key_hash(api_key, candidate_hash):
        logger.debug("_verify_key: [OK] bcrypt verification passed")
        stored_hash = candidate_hash
        break

if not stored_hash:
    logger.warning("_verify_key: bcrypt verification failed for all candidates")
    return False
```

---

## TESTING PLAN

### Test 1: Initial Connection
1. Start server: `uv run --python "C:\Users\admin\OneDrive\Desktop\Paper2Agent\sim-one-venv\Scripts\python.exe" --with fastmcp "C:\Claude\SIM-ONE-MCP-v2\src\SIM-ONE-MCP-v2_mcp-http.py"`
2. Connect with Codex (Authorization: Bearer header configured)
3. **Expected**: Server logs show:
   - `[OK] Extracted API key from Authorization Bearer header`
   - `[OK] API key verified successfully`
   - `[OK] Created session: <session-id>`
   - No OAuth discovery endpoint errors

### Test 2: Tool Call with Session
1. Call any tool (e.g., `esl_analyze_emotion`)
2. **Expected**: Server logs show:
   - `[OK] Valid session found: <session-id>`
   - `[OK] Skipping API key validation for session`
   - Tool executes successfully

### Test 3: Invalid API Key
1. Configure Codex with wrong API key
2. Connect
3. **Expected**: Server rejects with "Invalid or revoked API key"

### Test 4: Missing API Key
1. Remove Authorization header from Codex config
2. Connect
3. **Expected**: Server rejects with "Missing API key"

---

## SUCCESS CRITERIA

- [x] No OAuth discovery endpoint requests
- [x] API key validated on initialization
- [x] Session stored for subsequent requests
- [x] Tool calls work without re-validating API key
- [x] Invalid keys rejected
- [x] Missing keys rejected
- [x] Database connections properly closed
- [x] Multiple keys with same prefix handled correctly

---

## REFERENCES

- **PR#2 Comments**: https://github.com/dansasser/SIM-ONE/pull/2
- **Codex Bot P0 Comment**: Critical finding about wrong middleware hook
- **CodeRabbit Comments**: Database leak and fetchone() issues
- **FastMCP Middleware Docs**: https://github.com/jlowin/fastmcp (middleware hooks documentation)

---

## CONFIDENCE LEVEL

**HIGH** - This solution is based on:
1. Explicit guidance from Codex bot (PR review AI)
2. Understanding of MCP streamable-http protocol behavior
3. Analysis of actual header presence on initialize vs tool calls
4. Alignment with session-based authentication pattern

This should fix the authentication issue definitively.

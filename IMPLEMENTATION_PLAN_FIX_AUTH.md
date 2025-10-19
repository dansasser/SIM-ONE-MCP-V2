# Implementation Plan: Fix Middleware Authentication Header Access

**Date:** 2025-10-19
**Issue:** Middleware not receiving HTTP headers from Codex (X-API-Key)
**Root Cause:** Using wrong function to access headers in middleware context

---

## Problem Statement

**Current Behavior:**
- Codex sends request with `X-API-Key: sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk`
- Server receives HTTP request at transport layer
- Middleware calls `get_http_headers()` which returns empty dict
- Authentication fails with "Missing API key" error

**Root Cause:**
- `get_http_headers()` is a dependency injection helper for tools/routes
- Returns empty dict when called in middleware context without active request context
- Need to use `get_http_request()` instead to access Starlette Request object

**Verified Solution:**
- Use `get_http_request()` to get Starlette Request object
- Access headers via `request.headers.get()` or `dict(request.headers)`
- FastMCP docs confirm this works "anywhere within a request's execution flow, making it suitable for helper functions, nested calls, or middleware"

---

## The Fix

### File to Modify
`C:\Claude\SIM-ONE-MCP-V2\src\auth\auth_middleware.py`

### Current Code (Lines 20-27) - BROKEN:
```python
# Try to get headers
headers = {}
try:
    from fastmcp.server.dependencies import get_http_headers
    headers = get_http_headers()
except Exception:
    # If we can't get headers, reject
    raise ToolError("Authentication required - provide API key in Authorization or X-API-Key header")
```

### Fixed Code:
```python
# Get HTTP request object to access headers
from fastmcp.server.dependencies import get_http_request

try:
    request = get_http_request()
    headers = dict(request.headers)
except Exception:
    # If we can't get request, reject
    raise ToolError("Authentication required - provide API key in Authorization or X-API-Key header")
```

### What Changes:
1. Import `get_http_request` instead of `get_http_headers`
2. Call `get_http_request()` to get Starlette Request object
3. Extract headers dict using `dict(request.headers)`
4. Rest of middleware logic stays exactly the same

---

## Implementation Steps

### Step 1: Backup Current File
Create backup before making changes (optional but safe)

### Step 2: Update Import Statement
**Line 23:**
```python
# OLD:
from fastmcp.server.dependencies import get_http_headers

# NEW:
from fastmcp.server.dependencies import get_http_request
```

### Step 3: Update Header Access Code
**Lines 24-27:**
```python
# OLD:
headers = get_http_headers()

# NEW:
request = get_http_request()
headers = dict(request.headers)
```

### Step 4: Keep Error Handling Same
The try/except block and ToolError message stay identical.

---

## Complete Updated Method

```python
async def on_call_tool(self, context: MiddlewareContext, call_next):
    """Authenticate tool calls only (not protocol methods)."""

    # Get HTTP request object to access headers
    from fastmcp.server.dependencies import get_http_request

    try:
        request = get_http_request()
        headers = dict(request.headers)
    except Exception:
        # If we can't get request, reject
        raise ToolError("Authentication required - provide API key in Authorization or X-API-Key header")

    # Extract API key from headers
    auth_header = headers.get("authorization", "")
    api_key_header = headers.get("x-api-key", "")

    api_key = None

    # Check Authorization header (Bearer token)
    if auth_header.lower().startswith("bearer "):
        api_key = auth_header[7:].strip()
    # Check X-API-Key header
    elif api_key_header:
        api_key = api_key_header.strip()

    # No API key provided
    if not api_key:
        raise ToolError("Missing API key. Provide in Authorization (Bearer) or X-API-Key header")

    # Validate key format
    if not api_key.startswith("sk_simone_"):
        raise ToolError("Invalid API key format. Must start with 'sk_simone_'")

    # Verify key against database
    if not self._verify_key(api_key):
        raise ToolError("Invalid or revoked API key")

    # Key is valid, proceed
    return await call_next(context)
```

---

## Testing Plan

### Test 1: Valid API Key (Should SUCCEED)
**Setup:**
- Codex configured with: `X-API-Key = "sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk"`
- Server running on port 8000

**Expected:**
- Tool call succeeds
- Returns result from tool
- No authentication error

### Test 2: Missing API Key (Should FAIL)
**Setup:**
- Remove X-API-Key from Codex config
- Try to call tool

**Expected:**
- Returns error: "Missing API key. Provide in Authorization (Bearer) or X-API-Key header"

### Test 3: Invalid API Key (Should FAIL)
**Setup:**
- Codex configured with: `X-API-Key = "sk_simone_INVALID_KEY_12345678901234"`

**Expected:**
- Returns error: "Invalid or revoked API key"

### Test 4: Wrong Format (Should FAIL)
**Setup:**
- Codex configured with: `X-API-Key = "wrong_prefix_ABC123"`

**Expected:**
- Returns error: "Invalid API key format. Must start with 'sk_simone_'"

---

## Verification Checklist

After implementing fix:

- [ ] Server starts without errors
- [ ] All 8 tools visible in Codex
- [ ] Protocol methods work (initialize, ping, tools/list)
- [ ] Tool call with valid API key succeeds
- [ ] Tool call without API key rejected
- [ ] Tool call with invalid API key rejected
- [ ] Rate limiting still works
- [ ] last_used timestamp updates in database

---

## Rollback Plan

If fix doesn't work:

1. Revert `src/auth/auth_middleware.py` to previous version
2. Check server logs for new error messages
3. Report findings to user

**Previous working state:** Middleware was executing but couldn't access headers

---

## Why This Will Work

### Evidence from FastMCP Documentation:

**Quote from Context7 docs:**
> "This approach is versatile, working anywhere within a request's execution flow, making it suitable for helper functions, nested calls, or middleware."

This explicitly states `get_http_request()` works in middleware.

**Example from docs:**
```python
from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

request: Request = get_http_request()
user_agent = request.headers.get("user-agent", "Unknown")
```

### MCP JSON-RPC 2.0 Transport:

- Client sends: HTTP POST with headers
- Headers exist at HTTP transport layer
- FastMCP uses Starlette for HTTP handling
- Starlette Request object contains all headers
- `get_http_request()` returns this Request object

---

## Risk Assessment

**Risk Level:** LOW

**Why:**
- Small, isolated change (3 lines)
- No changes to database or other modules
- FastMCP docs explicitly confirm this approach
- Only affects header access, not business logic
- Easy rollback if needed

**Confidence:** HIGH - This is the correct fix per official documentation

---

## Files Modified

- `src/auth/auth_middleware.py` - Update header access method

## Files NOT Modified

- `src/SIM-ONE-MCP-v2_mcp-http.py` - No changes
- `src/auth/database.py` - No changes
- `src/auth/key_manager.py` - No changes
- `src/auth/rate_limiter.py` - No changes

---

## Notes

- Keep `database_token_verifier.py` file (don't delete)
- Don't review files in `src/STFO/` directory
- Don't start server without user approval
- Inform user and wait for approval before testing

---

**Status:** Ready for implementation
**Estimated Time:** 2 minutes to implement, 5 minutes to test

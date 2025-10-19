# Root Cause Analysis: Authentication Architecture Error
**Date:** 2025-10-19 11:05:00
**Issue:** API key authentication failing for MCP tool calls
**Status:** ROOT CAUSE IDENTIFIED

================================================================

## EXECUTIVE SUMMARY

The authentication system was implemented using the WRONG FastMCP pattern.

**Current Implementation:** Middleware (`on_call_tool` hook)
**Should Be:** Auth class (`verify_token` method)

**Why It Matters:** MCP streamable-http protocol sends custom headers (X-API-Key) ONLY during initialization, not with every tool call. Middleware executes on tool calls where headers don't exist. Auth executes during initialization where headers DO exist.

================================================================

## THE DISCOVERY PROCESS

### Attempt 1-5: Failed Authentication Approaches
See: `memory-bank/SIM-ONE-MCP-V2/activeContext.md` - Circular pattern documented

### Attempt 6: Fixed Header Access (Partial Success)
- Changed from `get_http_headers()` to `get_http_request()`
- Middleware CAN now access headers
- Added comprehensive logging
- **Result:** Middleware works, but headers aren't present

### Attempt 7: Tool Call Test (The Revelation)
Logs showed:
```
[OK] AUTH MIDDLEWARE: on_call_tool triggered
[OK] Got HTTP request object: <class 'starlette.requests.Request'>
[OK] Extracted headers dict with 5 headers
[OK] Headers: ['accept', 'mcp-session-id', 'content-type', 'host', 'content-length']
[FAIL] No API key found in either header
```

**Critical Observation:** X-API-Key is MISSING from tool call requests!

### Attempt 8: MCP Protocol Research (Root Cause Found)

Researched MCP streamable-http specification (2025-06-18):

**Protocol Behavior:**
1. Client sends initial POST /mcp with custom headers (X-API-Key)
2. Server responds with `mcp-session-id`
3. Client sends subsequent requests with ONLY `mcp-session-id` (NO custom headers)

**Why Custom Headers Aren't Forwarded:**
- MCP spec requires: `Accept`, `Content-Type`, `Mcp-Session-Id`
- Custom headers (X-API-Key) are NOT part of the protocol spec
- Session-based authentication is the intended pattern

================================================================

## THE FUNDAMENTAL MISTAKE

We implemented authentication at the WRONG layer:

### What We Did (WRONG):
```python
# src/SIM-ONE-MCP-v2_mcp-http.py
from auth.auth_middleware import APIKeyAuthenticationMiddleware

mcp = FastMCP(name="SIM-ONE-MCP-v2")
mcp.add_middleware(APIKeyAuthenticationMiddleware())  # ← Runs on TOOL CALLS
```

**When Middleware Executes:**
- Triggered by: Tool calls (`tools/call`)
- Headers present: `mcp-session-id`, standard HTTP headers
- Headers MISSING: `X-API-Key`, `Authorization`
- Result: FAILS - no API key to verify

### What We Should Do (CORRECT):
```python
# src/SIM-ONE-MCP-v2_mcp-http.py
from auth.database_token_verifier import DatabaseTokenVerifier

mcp = FastMCP(
    name="SIM-ONE-MCP-v2",
    auth=DatabaseTokenVerifier()  # ← Runs during INITIALIZATION
)
```

**When Auth Executes:**
- Triggered by: Initial connection (`initialize` request)
- Headers present: `X-API-Key`, `Authorization`, all custom headers
- Process: Verify API key, return AccessToken
- Session: AccessToken persists for entire session
- Result: SUCCESS - API key verified once, session authenticated

================================================================

## TECHNICAL DETAILS

### FastMCP Auth Class Pattern:

```python
class DatabaseTokenVerifier(Auth):
    def verify_token(self, token: str) -> AccessToken | None:
        # Called during INITIALIZATION with X-API-Key from headers
        # Returns AccessToken if valid, None if invalid
        # AccessToken persists for the session
```

**Flow:**
1. Client connects with `X-API-Key: sk_simone_...`
2. FastMCP extracts token from `X-API-Key` or `Authorization: Bearer` header
3. Calls `verify_token(token)`
4. If returns AccessToken: Session authenticated
5. If returns None: Connection rejected
6. All subsequent tool calls use authenticated session

### FastMCP Middleware Pattern:

```python
class APIKeyAuthenticationMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        # Called on EVERY TOOL CALL (not initialization)
        # X-API-Key header NOT present in tool calls
        # Only mcp-session-id header present
```

**Flow:**
1. Client connects and initializes (X-API-Key sent but ignored)
2. Session created with mcp-session-id
3. Client calls tool with mcp-session-id (NO X-API-Key)
4. Middleware executes, looks for X-API-Key
5. Header missing → Authentication fails
6. Tool call rejected

================================================================

## WHY THIS HAPPENED

### The Confusion:

1. **Both patterns LOOK similar:**
   - Both check API keys
   - Both verify against database
   - Both use similar code logic

2. **Documentation wasn't clear:**
   - FastMCP docs show both approaches
   - Didn't emphasize when to use which
   - MCP protocol spec separate from FastMCP docs

3. **Initial implementation choice:**
   - Middleware seemed more flexible
   - Appeared to give per-request control
   - Didn't understand protocol header behavior

### The Learning:

**MCP Protocol Insight:**
- HTTP transport is session-based, not request-based
- Authentication happens ONCE at connection time
- Session ID tracks authenticated sessions
- Custom headers only on initial connection

**FastMCP Pattern Insight:**
- `auth=` parameter: For connection-level authentication
- `add_middleware()`: For per-request processing (after auth)
- Use Auth for authentication, Middleware for authorization/logging

================================================================

## THE EXISTING SOLUTION

**File:** `src/auth/database_token_verifier.py`

This file ALREADY implements the correct pattern!
It was created earlier but NEVER USED.

**What It Does:**
1. Extends FastMCP's `Auth` class
2. Implements `verify_token(token)` method
3. Verifies API key against database with bcrypt
4. Checks rate limits
5. Returns AccessToken with user claims
6. Handles both `X-API-Key` and `Authorization: Bearer` headers

**Status:** Complete, tested (in isolation), ready to use

================================================================

## THE FIX

### Step 1: Update Server File

**File:** `src/SIM-ONE-MCP-v2_mcp-http.py`

**Current Code (lines 24-35):**
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

**New Code:**
```python
# Import authentication
from auth.database import init_database
from auth.database_token_verifier import DatabaseTokenVerifier

# Initialize database
init_database()

# Server definition with authentication
mcp = FastMCP(
    name="SIM-ONE-MCP-v2",
    auth=DatabaseTokenVerifier()
)

# NOTE: Middleware removed - authentication now handled by Auth class
```

### Step 2: Optional - Add Logging Middleware

If we want to keep logging for monitoring:

```python
class LoggingMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        """Log tool calls for monitoring (authentication already done)."""
        logger.info(f"Tool called: {context.message.name}")

        # Get authenticated user from context
        access_token = get_access_token()
        if access_token:
            logger.info(f"Authenticated user: {access_token.claims.get('email')}")

        return await call_next(context)

mcp.add_middleware(LoggingMiddleware())
```

### Step 3: Test

1. Restart server
2. Connect with Codex
3. Call a tool
4. Should succeed with API key from initialization

================================================================

## VERIFICATION

### What Should Happen:

**Connection Phase:**
```
Client → Server: POST /mcp (initialize)
Headers: X-API-Key: sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk

Server: Calls DatabaseTokenVerifier.verify_token()
Server: Validates key against database
Server: Returns mcp-session-id with authenticated session

Client ← Server: 200 OK with session ID
```

**Tool Call Phase:**
```
Client → Server: POST /mcp (tools/call)
Headers: Mcp-Session-Id: <session-id>

Server: Session already authenticated
Server: Executes tool
Server: Returns result

Client ← Server: 200 OK with tool result
```

### Logs to Expect:

**On Connection:**
- Database query for API key prefix
- bcrypt verification
- Rate limit check
- Session created with user claims

**On Tool Call:**
- No authentication logs (already authenticated)
- Tool execution logs
- Optional: User identification from session claims

================================================================

## LESSONS LEARNED

1. **Read Protocol Specs First**
   - MCP spec defines session-based authentication
   - Custom headers only on initialization
   - Understanding protocol prevents wrong patterns

2. **Understand Framework Patterns**
   - FastMCP Auth = connection authentication
   - FastMCP Middleware = per-request processing
   - Use each for its intended purpose

3. **Test Authentication Flow Early**
   - Don't assume header forwarding
   - Log headers at each phase
   - Verify protocol behavior matches expectations

4. **Trust Existing Code**
   - DatabaseTokenVerifier was correct all along
   - Should have been used from the start
   - Sometimes the answer is already written

================================================================

## FILES INVOLVED

### Will Be Used (Correct):
- `src/auth/database_token_verifier.py` - Auth implementation ✓
- `src/auth/database.py` - Database operations ✓
- `src/auth/key_manager.py` - Key hashing/verification ✓
- `src/auth/rate_limiter.py` - Rate limiting ✓

### Will Be Removed (Incorrect):
- `src/auth/auth_middleware.py` - Middleware approach ✗

### Will Be Modified:
- `src/SIM-ONE-MCP-v2_mcp-http.py` - Use Auth instead of Middleware

================================================================

## TIMELINE

**2025-10-18:** Initial authentication implementation (wrong pattern)
**2025-10-19 10:55:** Server logs show successful connection, no auth logs
**2025-10-19 11:04:** Tool call attempt reveals missing headers
**2025-10-19 11:05:** MCP spec research identifies root cause
**2025-10-19 11:10:** Solution documented (this file)

**Estimated Fix Time:** 2 minutes (1 file change)
**Estimated Test Time:** 5 minutes

================================================================

STATUS: Ready for implementation
CONFIDENCE: HIGH - Protocol spec confirms this is the correct pattern
RISK: LOW - Simple change, existing Auth implementation already complete

# TODO: SIM-ONE-MCP-V2

**Project Directory:** C:\Claude\SIM-ONE-MCP-V2
**Current Working Directory:** C:\Claude
**Date Created:** 2025-10-19
**Last Updated:** 2025-10-19 16:45

---

## Current Context

**BREAKTHROUGH DISCOVERY** from PR#2 review comments (Codex Bot P0 Critical Finding):

The authentication was failing because middleware was using the WRONG HOOK. The `on_call_tool` hook runs AFTER MCP initialization, but custom headers (X-API-Key, Authorization) are ONLY present on the initial `initialize` request. Subsequent tool calls carry ONLY `mcp-session-id` header.

**Root Cause:**
- Middleware uses `async def on_call_tool(...)` hook
- This hook executes on tool calls (AFTER initialization)
- At tool call time, X-API-Key and Authorization headers are GONE
- Only mcp-session-id is present
- Current code fails with "Missing API key" on every tool call

**The Solution:**
1. Change middleware hook from `on_call_tool` to `on_request`
2. Implement session storage (mcp-session-id -> api_key_hash mapping)
3. Validate API key on FIRST request (initialize)
4. Store session ID for subsequent requests
5. On tool calls, check session ID instead of re-validating API key

**Implementation Plan:** AUTHENTICATION_FIX_PLAN_V4.md

**Code Reset:** Branch reset to remote `claude/fix-session-based-auth` (commit 28be263)

---

## Tasks

### In Progress

- [ ] IN_PROGRESS: Update SIM-ONE-MCP-V2-TODO.md with new implementation tasks

### Pending

#### Implementation Tasks

- [ ] PENDING: Change auth_middleware.py hook from on_call_tool to on_request
  - File: `src/auth/auth_middleware.py`
  - Line 19: Add `__init__` method with `self.sessions = {}`
  - Line 25: Change `async def on_call_tool` to `async def on_request`
  - Line 30: Add session validation logic BEFORE API key check
  - Line 91: Add session storage after successful API key validation
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Step 1

- [ ] PENDING: Implement session storage (mcp-session-id -> api_key_hash mapping)
  - File: `src/auth/auth_middleware.py`
  - Add: `self.sessions = {}` to `__init__`
  - Add: Check for `mcp-session-id` in headers at start of `on_request`
  - Add: If valid session found, skip API key validation
  - Add: Store session after successful API key validation
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Step 1

- [ ] PENDING: Add session validation logic to middleware
  - File: `src/auth/auth_middleware.py`
  - Logic: Check `headers.get("mcp-session-id")` first
  - If session exists in cache: Allow request without API key check
  - If no session: Require API key validation
  - Store session ID after successful API key validation
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Step 1

- [ ] PENDING: Fix database connection leak in _verify_key method
  - File: `src/auth/auth_middleware.py`
  - Line 110-122: Wrap database operations in try/finally
  - Ensure `conn.close()` always called even on exception
  - Issue: CodeRabbit identified connection not closed on error
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Step 2

- [ ] PENDING: Fix fetchone() bug - use fetchall() with iteration
  - File: `src/auth/auth_middleware.py`
  - Line 123-135: Change `fetchone()` to `fetchall()`
  - Iterate through all matching rows
  - Verify each candidate with bcrypt until match found
  - Issue: key_prefix may match multiple rows (non-unique)
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Step 3

#### Testing Tasks

- [ ] PENDING: Test server with Codex - verify initialization succeeds
  - Start server: `uv run --python "C:\Users\admin\OneDrive\Desktop\Paper2Agent\sim-one-venv\Scripts\python.exe" --with fastmcp "C:\Claude\SIM-ONE-MCP-v2\src\SIM-ONE-MCP-v2_mcp-http.py"`
  - Connect with Codex (Authorization: Bearer header configured)
  - Expected: Server logs show API key validated, session created
  - Expected: NO OAuth discovery endpoint errors
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Test 1

- [ ] PENDING: Test server with Codex - verify tool calls work
  - Call any tool (e.g., `esl_analyze_emotion`)
  - Expected: Server logs show session validation (not API key re-check)
  - Expected: Tool executes successfully
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Test 2

- [ ] PENDING: Test invalid API key rejection
  - Configure Codex with wrong API key
  - Expected: Server rejects with "Invalid or revoked API key"
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Test 3

- [ ] PENDING: Test missing API key rejection
  - Remove Authorization header from Codex config
  - Expected: Server rejects with "Missing API key"
  - Reference: AUTHENTICATION_FIX_PLAN_V4.md Test 4

#### Git Tasks

- [ ] PENDING: Commit working authentication implementation
  - Files to commit:
    - `src/auth/auth_middleware.py` (updated with on_request hook + sessions)
    - `AUTHENTICATION_FIX_PLAN_V4.md` (new plan)
  - Message: "fix: use on_request hook for session-based auth"

- [ ] PENDING: Update PR #2 with working solution
  - PR: https://github.com/dansasser/SIM-ONE-MCP-V2/pull/2
  - Push changes to `claude/fix-session-based-auth` branch
  - Reference Codex bot comment in PR update

### Completed

- [x] COMPLETED: Read PR#2 comments from CodeRabbit and Codex bots (2025-10-19 16:20)
- [x] COMPLETED: Discovered critical P0 finding from Codex bot (2025-10-19 16:20)
- [x] COMPLETED: Reset to remote branch claude/fix-session-based-auth (2025-10-19 16:25)
- [x] COMPLETED: Analyzed breakthrough discovery and root cause (2025-10-19 16:30)
- [x] COMPLETED: Create AUTHENTICATION_FIX_PLAN_V4.md with breakthrough solution (2025-10-19 16:40)
- [x] COMPLETED: Deep research into FastMCP and official MCP SDK authentication (2025-10-19 13:00)
- [x] COMPLETED: Analyze official SDK examples and extract patterns (2025-10-19 13:00)
- [x] COMPLETED: Create comprehensive implementation plan V3 (2025-10-19 13:00)
- [x] COMPLETED: Document findings and research (2025-10-19 13:15)
- [x] COMPLETED: User updated Codex config to Authorization Bearer header (2025-10-19 13:25)

---

## Notes

### The Breakthrough Discovery (Codex Bot P0 Comment)

**Exact Quote from PR#2 Review:**
> "The middleware authenticates inside `on_call_tool` by reading the `Authorization`/`X-API-Key` headers for every tool invocation. In the MCP streamable-http transport those headers are only present on the initial `initialize` request; subsequent tool calls carry only `mcp-session-id`. Because the code here executes after initialization, every tool call will take the `Missing API key` branch and raise a `ToolError`, making the server unusable even when the client supplied a valid key. Authentication needs to occur in an `on_request` hook (or store the validated session id from initialization) so that later tool calls are permitted without re-sending the key."

### Why ALL Previous Attempts Failed

**TokenVerifier Approach (V3):**
- Used `auth=` parameter with `TokenVerifier`
- Triggered OAuth 2.1 discovery endpoints
- FastMCP expected full OAuth implementation
- WRONG for simple API key authentication

**BearerAuthProvider Approach:**
- Tried using `BearerAuthProvider` from fastmcp.server.auth.providers.bearer
- Also triggered OAuth discovery
- Required RSAKeyPair and JWT infrastructure
- WRONG for simple API key authentication

**Middleware with on_call_tool Hook (Current):**
- Runs AFTER initialization (too late!)
- X-API-Key and Authorization headers NOT present at tool call time
- Every tool call fails with "Missing API key"
- CORRECT approach (middleware) but WRONG hook

### The Correct Pattern (V4 - Session-Based)

**MCP streamable-http Protocol:**
```
Initialize Request:
  Headers: Authorization: Bearer <key>, X-API-Key: <key>
  Response: Creates mcp-session-id

Tool Call Requests:
  Headers: mcp-session-id: <id>
  NO Authorization or X-API-Key headers!
```

**Middleware Flow (CORRECT):**
```python
async def on_request(self, context, call_next):  # ← RIGHT HOOK
    # 1. Check for session ID
    session_id = headers.get("mcp-session-id")

    if session_id and session_id in self.sessions:
        # Valid session - allow without API key check
        return await call_next(context)

    # 2. No session - require API key
    api_key = extract_api_key(headers)
    verify_api_key(api_key)

    # 3. Store session for future requests
    if session_id:
        self.sessions[session_id] = api_key_hash
```

### Key Files

**Implementation:**
- `src/auth/auth_middleware.py` - NEEDS UPDATES (on_request hook + sessions)
- `src/SIM-ONE-MCP-v2_mcp-http.py` - CORRECT (uses middleware)

**Plans:**
- `AUTHENTICATION_FIX_PLAN_V4.md` - **CURRENT PLAN** (session-based approach)
- `AUTHENTICATION_IMPLEMENTATION_PLAN_V3.md` - Outdated (TokenVerifier approach)
- `AUTHENTICATION_RESEARCH_FINDINGS.md` - Research notes

**Database:**
- `C:\Claude\SIM-ONE-MCP-V2\data\api_keys.db`
- Active key: `sk_simone_EXAMPLE_KEY_HERE` (use actual key from database)

**Venv:**
- `C:\Users\admin\OneDrive\Desktop\Paper2Agent\sim-one-venv`
- FastMCP 2.12.4 installed

### Expected Behavior After Fix

**Successful Authentication Flow:**
```
[Initialize Request]
[OK] Extracted API key from Authorization Bearer header
[OK] API key verified successfully
[OK] Created session: 7a4f9b2c1d8e...

[Tool Call Request #1]
[OK] Valid session found: 7a4f9b2c1d8e...
[OK] Skipping API key validation for session
[TOOL] Executing: five_laws_validate_text
[TOOL] Completed successfully

[Tool Call Request #2]
[OK] Valid session found: 7a4f9b2c1d8e...
[OK] Skipping API key validation for session
[TOOL] Executing: esl_analyze_emotion
[TOOL] Completed successfully
```

**Failed Authentication:**
```
[Initialize Request with invalid key]
[FAIL] bcrypt verification failed
401 Unauthorized - Invalid or revoked API key
```

---

## Blockers

None - Clear path forward with session-based approach.

---

## User Actions Required

⏳ Review AUTHENTICATION_FIX_PLAN_V4.md
⏳ Approve implementation of fixes
⏳ Test authentication after implementation
⏳ Confirm all tools work correctly

---

**Status:** Ready to implement session-based authentication fix
**Confidence:** 99% - Solution directly from PR review bot analysis
**Time Estimate:** 30-45 minutes total (implementation + testing)

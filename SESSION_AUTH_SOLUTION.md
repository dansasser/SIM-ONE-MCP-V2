# Session-Based Authentication Solution

**Date:** 2025-10-19 11:15
**Hook:** `on_request` (runs for ALL requests)
**Strategy:** Validate API key on first request, store session ID, check session on subsequent requests

---

## Why This is DIFFERENT:

We tried:
- ❌ Auth class (doesn't exist - ImportError)
- ❌ Middleware `on_call_tool` (runs too late - X-API-Key already gone)

We NEVER tried:
- ✅ Middleware `on_request` (runs for ALL requests including initialization)

---

## How It Works:

```
Request 1 (initialize):
  → Client sends X-API-Key
  → Middleware on_request fires
  → Extract X-API-Key
  → Validate against database
  → Get mcp-session-id from context
  → Store session as authenticated

Request 2+ (tool calls):
  → Client sends mcp-session-id
  → Middleware on_request fires
  → Check if session ID is authenticated
  → Allow or deny request
```

---

## Implementation:

```python
class SessionAuthMiddleware(Middleware):
    def __init__(self):
        # Store authenticated session IDs
        self.authenticated_sessions = set()

    async def on_request(self, context: MiddlewareContext, call_next):
        # Get HTTP headers
        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        headers = dict(request.headers)

        # Check for X-API-Key (initialization/first request)
        api_key = headers.get("x-api-key") or headers.get("authorization", "").replace("Bearer ", "")

        if api_key:
            # Validate API key
            if self._verify_key(api_key):
                # Get session ID and mark as authenticated
                session_id = headers.get("mcp-session-id")
                if session_id:
                    self.authenticated_sessions.add(session_id)
                    logger.info(f"[OK] Session authenticated: {session_id[:8]}...")
            else:
                raise ToolError("Invalid or revoked API key")
        else:
            # No API key - check if session is authenticated
            session_id = headers.get("mcp-session-id")
            if session_id not in self.authenticated_sessions:
                raise ToolError("Unauthenticated session - API key required")

        return await call_next(context)
```

---

## Why This Works:

1. **`on_request` runs for ALL requests** - initialization AND tool calls
2. **Session ID persists** - Same session ID for entire connection
3. **Store state in middleware instance** - authenticated_sessions set
4. **Check appropriate header** - X-API-Key on first, session ID on rest

---

STATUS: This is a NEW approach we haven't tried. It uses middleware (which works) but the RIGHT hook.

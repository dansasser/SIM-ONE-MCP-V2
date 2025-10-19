# SIM-ONE MCP Server - Active Configuration

## Active Server File
**File:** `src/SIM-ONE-MCP-v2_mcp-http-with-rest.py`

This is the PRODUCTION server file. Do NOT confuse with test files.

## Start Command
```bash
fastmcp run src.SIM-ONE-MCP-v2_mcp-http-with-rest:app --port 8000
```

## Server Architecture
- **FastAPI app** at root level with authentication middleware
- **FastMCP instance** mounted at `/mcp` endpoint
- **REST test endpoints** at `/test/*`

## Authentication
- Database: `data/api_keys.db`
- Middleware: `src/auth/middleware.py` (APIKeyAuthMiddleware)
- FastMCP middleware: `src/auth/fastmcp_auth_middleware.py` (currently added but causing 400 errors)

## Current Issues
- FastMCP middleware implementation has bugs
- Using `get_http_headers()` in wrong context (middleware vs tools)
- Using `ToolError` in `on_request` (should be for `on_call_tool`)
- Authentication should use FastMCP's `auth` parameter, not custom middleware

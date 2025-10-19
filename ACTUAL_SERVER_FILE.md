# ACTUAL SERVER FILE IN USE

## DO NOT FORGET THIS

**Active Server File:** `src/SIM-ONE-MCP-v2_mcp-http.py`

**NOT:**
- ❌ `src/SIM-ONE-MCP-v2_mcp-http-with-rest.py` (test file)
- ❌ `src/SIM-ONE-MCP-v2_mcp-http_with_test.py` (test file)
- ❌ `src/SIM-ONE-MCP-v2_mcp.py` (old version)

## Start Command
```bash
fastmcp run src.SIM-ONE-MCP-v2_mcp-http:mcp --port 8000
```

## Current State
- Uses `APIKeyAuthMiddleware` passed to `mcp.run(middleware=[...])`
- Does NOT import `fastmcp_auth_middleware.py`
- Pure FastMCP server, no FastAPI wrapper

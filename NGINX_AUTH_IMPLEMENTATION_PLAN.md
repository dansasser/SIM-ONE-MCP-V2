# Nginx Proxy Authentication Implementation Plan

## Architecture Overview

```
Client Request
    |
    v
Nginx (Port 80/443)
    |
    |---> Auth Service (Port 9000) - Verifies API key against SQLite
    |           |
    |           v
    |       [PASS] Continue to FastMCP
    |       [FAIL] Return 401 Unauthorized
    |
    v
FastMCP Server (Port 8000) - No auth, just tools
```

## Components

### 1. FastMCP Server (Port 8000)
**Status:** COMPLETED
**File:** `src/SIM-ONE-MCP-v2_mcp-http.py`
**Purpose:** Minimal MCP server with no authentication
**Changes Made:**
- Removed all authentication code
- Kept detailed HTTP logging middleware
- Uses `asyncio.run(mcp.run_async())` pattern from Google tutorial
- Listens on port 8000 (localhost only, not exposed externally)

### 2. Auth Service (Port 9000)
**Status:** TO BE CREATED
**File:** `src/auth_service.py` (new file)
**Purpose:** Lightweight FastAPI app that validates API keys for nginx
**Requirements:**
- Single endpoint: `GET /verify`
- Reads API key from headers (X-API-Key or Authorization Bearer)
- Queries SQLite database using existing DatabaseTokenVerifier
- Returns 200 OK (valid) or 401 Unauthorized (invalid)
- Fast response time (< 50ms) for nginx auth_request
- Detailed logging for debugging

**Implementation:**
```python
# auth_service.py
from fastapi import FastAPI, Header, HTTPException
from auth.database_token_verifier import DatabaseTokenVerifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
verifier = DatabaseTokenVerifier()

@app.get("/verify")
async def verify_token(
    x_api_key: str = Header(None),
    authorization: str = Header(None)
):
    logger.info(f"Auth request - X-API-Key: {bool(x_api_key)}, Authorization: {bool(authorization)}")

    # Extract token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        logger.info("Using Bearer token from Authorization header")
    elif x_api_key:
        token = x_api_key
        logger.info("Using token from X-API-Key header")

    if not token:
        logger.warning("No API key provided")
        raise HTTPException(status_code=401, detail="No API key provided")

    # Verify against database
    access_token = await verifier.verify_token(token)

    if not access_token:
        logger.warning(f"Invalid API key: {token[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.info(f"Valid API key for client: {access_token.claims.get('sub')}")
    return {"status": "authorized", "client_id": access_token.claims.get("sub")}

if __name__ == "__main__":
    import uvicorn
    print("="*80)
    print("SIM-ONE Auth Service")
    print("="*80)
    print("Endpoint: http://127.0.0.1:9000/verify")
    print("Purpose: Validates API keys for nginx auth_request")
    print("Database: SQLite (via DatabaseTokenVerifier)")
    print("="*80)
    uvicorn.run(app, host="127.0.0.1", port=9000)
```

### 3. Nginx Configuration
**Status:** TO BE CREATED
**File:** `nginx/nginx.conf` (new file)
**Purpose:** Reverse proxy with auth_request to auth service
**Requirements:**
- Listen on port 80 (external)
- Forward `/mcp` requests to FastMCP on port 8000
- Check auth via auth service on port 9000 BEFORE forwarding
- Pass through all headers and body
- Return proper error responses

**Implementation:**
```nginx
events {
    worker_connections 1024;
}

http {
    # Upstream for FastMCP server (no auth)
    upstream fastmcp {
        server 127.0.0.1:8000;
    }

    # Upstream for auth service
    upstream auth {
        server 127.0.0.1:9000;
    }

    server {
        listen 80;
        server_name localhost;

        # MCP endpoint with authentication
        location /mcp {
            # STEP 1: Check authentication
            auth_request /auth-verify;

            # STEP 2: If auth passes, proxy to FastMCP
            proxy_pass http://fastmcp/mcp;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # Pass through auth headers
            proxy_set_header X-API-Key $http_x_api_key;
            proxy_set_header Authorization $http_authorization;

            # Timeout settings
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Internal auth verification endpoint
        location = /auth-verify {
            internal;  # Not accessible from outside

            proxy_pass http://auth/verify;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";

            # Forward auth headers to auth service
            proxy_set_header X-API-Key $http_x_api_key;
            proxy_set_header Authorization $http_authorization;
        }

        # Health check endpoint (no auth required)
        location /health {
            proxy_pass http://fastmcp/health;
        }
    }
}
```

### 4. Docker Compose (Optional)
**Status:** TO BE CREATED
**File:** `docker-compose.yml` (new file)
**Purpose:** Run all three services together
**Requirements:**
- Service 1: FastMCP (port 8000, internal only)
- Service 2: Auth Service (port 9000, internal only)
- Service 3: Nginx (port 80, exposed externally)
- Shared volume for SQLite database

**Implementation:**
```yaml
version: '3.8'

services:
  fastmcp:
    build:
      context: .
      dockerfile: Dockerfile.fastmcp
    ports:
      - "8000:8000"  # Internal only
    volumes:
      - ./src:/app/src
      - ./data:/app/data
    environment:
      - PYTHONUNBUFFERED=1
    command: python src/SIM-ONE-MCP-v2_mcp-http.py
    networks:
      - internal

  auth-service:
    build:
      context: .
      dockerfile: Dockerfile.auth
    ports:
      - "9000:9000"  # Internal only
    volumes:
      - ./src:/app/src
      - ./data:/app/data
    environment:
      - PYTHONUNBUFFERED=1
    command: python src/auth_service.py
    networks:
      - internal

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"  # Exposed externally
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - fastmcp
      - auth-service
    networks:
      - internal

networks:
  internal:
    driver: bridge
```

## Implementation Steps

### Phase 1: Create Auth Service
1. Create `src/auth_service.py`
2. Test auth service independently:
   ```bash
   python src/auth_service.py
   # Test with curl:
   curl -H "X-API-Key: valid-key-from-db" http://127.0.0.1:9000/verify
   ```
3. Verify it can read from SQLite database
4. Verify response times (should be < 50ms)

### Phase 2: Configure Nginx
1. Install nginx (if not already installed):
   ```bash
   # Windows
   choco install nginx

   # Linux
   sudo apt-get install nginx
   ```
2. Create `nginx/nginx.conf` with configuration above
3. Test nginx config:
   ```bash
   nginx -t -c C:/Claude/SIM-ONE-MCP-V2/nginx/nginx.conf
   ```
4. Start nginx with custom config:
   ```bash
   nginx -c C:/Claude/SIM-ONE-MCP-V2/nginx/nginx.conf
   ```

### Phase 3: Integration Testing
1. Start all three services:
   ```bash
   # Terminal 1: FastMCP
   python src/SIM-ONE-MCP-v2_mcp-http.py

   # Terminal 2: Auth Service
   python src/auth_service.py

   # Terminal 3: Nginx
   nginx -c C:/Claude/SIM-ONE-MCP-V2/nginx/nginx.conf
   ```

2. Test with valid API key:
   ```bash
   curl -H "X-API-Key: valid-key" http://localhost/mcp
   ```
   Expected: 200 OK, MCP response

3. Test with invalid API key:
   ```bash
   curl -H "X-API-Key: invalid-key" http://localhost/mcp
   ```
   Expected: 401 Unauthorized

4. Test with no API key:
   ```bash
   curl http://localhost/mcp
   ```
   Expected: 401 Unauthorized

5. Test tool execution through nginx:
   ```bash
   # Use MCP client to connect through nginx
   # Should now successfully execute tools
   ```

### Phase 4: Verify Tool Execution
1. Use Codex to connect to nginx endpoint (http://localhost/mcp)
2. List tools (should work)
3. Execute a tool (THIS SHOULD NOW WORK)
4. Check logs from all three services:
   - Nginx: Request routing
   - Auth Service: Token verification
   - FastMCP: Tool execution

## Benefits of This Architecture

1. **Separation of Concerns**
   - FastMCP: Only handles MCP protocol and tools
   - Auth Service: Only handles authentication
   - Nginx: Only handles routing and proxying

2. **Follows Google Tutorial Pattern**
   - FastMCP is minimal (like tutorial)
   - Authentication is external (like Cloud Run proxy)
   - Clean, simple implementation

3. **Debugging**
   - Each service logs independently
   - Can test each component separately
   - Easy to identify where problems occur

4. **Scalability**
   - Can run multiple FastMCP instances behind nginx
   - Auth service can be optimized independently
   - Can add rate limiting, caching, etc. at nginx layer

5. **Security**
   - FastMCP not exposed externally (port 8000 blocked)
   - Auth Service not exposed externally (port 9000 blocked)
   - Only nginx port 80 accessible from outside
   - SQLite database queries isolated to auth service

## File Structure After Implementation

```
SIM-ONE-MCP-V2/
├── src/
│   ├── SIM-ONE-MCP-v2_mcp-http.py (UPDATED - no auth)
│   ├── auth_service.py (NEW)
│   ├── auth/
│   │   ├── database.py (existing)
│   │   └── database_token_verifier.py (existing)
│   └── tools/ (existing)
├── nginx/
│   └── nginx.conf (NEW)
├── docker-compose.yml (NEW - optional)
├── Dockerfile.fastmcp (NEW - optional)
├── Dockerfile.auth (NEW - optional)
└── NGINX_AUTH_IMPLEMENTATION_PLAN.md (this file)
```

## Testing Checklist

- [ ] Auth service starts successfully
- [ ] Auth service responds to /verify endpoint
- [ ] Auth service validates valid API keys (200 OK)
- [ ] Auth service rejects invalid API keys (401 Unauthorized)
- [ ] Nginx starts with custom config
- [ ] Nginx proxies requests to FastMCP after auth success
- [ ] Nginx blocks requests with invalid/missing API keys
- [ ] FastMCP receives requests from nginx (check logs)
- [ ] Tools list successfully through nginx
- [ ] **Tools execute successfully through nginx** (MAIN GOAL)
- [ ] All three services log appropriately
- [ ] Can test each service independently

## Rollback Plan

If nginx approach doesn't work:
1. Keep `feature/nginx-proxy-auth` branch
2. Switch back to previous branch
3. Document what went wrong in this file
4. Try alternative approach (Python auth proxy, etc.)

## Next Steps

1. Create auth_service.py
2. Test auth service independently
3. Create nginx.conf
4. Test nginx config
5. Integration test all three services
6. **VERIFY TOOLS EXECUTE** (the ultimate goal)

"""
Authentication middleware for MCP server.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from .key_manager import verify_key_hash, hash_api_key
from .rate_limiter import check_rate_limit
from .database import get_db_connection


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate API requests using API keys.
    Checks Authorization or X-API-Key headers.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and check API key."""
        
        # Extract API key from headers
        auth_header = request.headers.get("Authorization", "")
        api_key_header = request.headers.get("X-API-Key", "")
        
        api_key = None
        
        # Check Authorization header (Bearer token)
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:].strip()
        # Check X-API-Key header
        elif api_key_header:
            api_key = api_key_header.strip()
        
        # No API key provided
        if not api_key:
            return JSONResponse(
                {
                    "error": "Missing API key",
                    "message": "Provide API key in Authorization header (Bearer token) or X-API-Key header"
                },
                status_code=401
            )
        
        # Validate key format
        if not api_key.startswith("sk_simone_"):
            return JSONResponse(
                {
                    "error": "Invalid API key format",
                    "message": "API key must start with 'sk_simone_'"
                },
                status_code=401
            )
        
        # Verify key against database
        key_valid, key_hash = self._verify_key(api_key)
        
        if not key_valid:
            return JSONResponse(
                {
                    "error": "Invalid API key",
                    "message": "The provided API key is invalid or has been revoked"
                },
                status_code=401
            )
        
        # Check rate limit
        if not check_rate_limit(key_hash):
            return JSONResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Rate limit: 1000 requests per hour"
                },
                status_code=429
            )
        
        # Update last used timestamp
        from .database import update_last_used
        update_last_used(key_hash)
        
        # Key is valid, proceed with request
        response = await call_next(request)
        return response
    
    def _verify_key(self, api_key: str) -> tuple[bool, str]:
        """
        Verify API key against database.
        Returns (is_valid, key_hash)
        """
        # Get all active keys from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key_hash FROM api_keys
            WHERE is_active = 1
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Check each hash
        for row in rows:
            stored_hash = row['key_hash']
            if verify_key_hash(api_key, stored_hash):
                return True, stored_hash
        
        return False, ""


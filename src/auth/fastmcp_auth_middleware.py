"""
FastMCP authentication middleware for API key verification.
"""
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError
from .key_manager import verify_key_hash, get_key_prefix
from .database import get_db_connection


class FastMCPAPIKeyAuthMiddleware(Middleware):
    """
    FastMCP middleware to authenticate API requests using API keys.
    Checks Authorization or X-API-Key headers.
    """

    async def on_request(self, context: MiddlewareContext, call_next):
        """Process the request and check API key."""

        # Get HTTP headers from FastMCP context
        headers = get_http_headers()

        # Extract API key from headers (case-insensitive)
        auth_header = headers.get("authorization", "")
        api_key_header = headers.get("x-api-key", "")

        api_key = None

        # Check Authorization header (Bearer token) - case insensitive
        if auth_header.lower().startswith("bearer "):
            api_key = auth_header[7:].strip()
        # Check X-API-Key header
        elif api_key_header:
            api_key = api_key_header.strip()

        # No API key provided
        if not api_key:
            raise ToolError("Missing API key. Provide API key in Authorization header (Bearer token) or X-API-Key header")

        # Validate key format
        if not api_key.startswith("sk_simone_"):
            raise ToolError("Invalid API key format. API key must start with 'sk_simone_'")

        # Verify key against database
        key_valid, key_hash = self._verify_key(api_key)

        if not key_valid:
            raise ToolError("Invalid API key. The provided API key is invalid or has been revoked")

        # Store authenticated key info in context for tools to use if needed
        if hasattr(context, 'fastmcp_context') and context.fastmcp_context:
            context.fastmcp_context.set_state("api_key_hash", key_hash)

        # Key is valid, proceed with request
        return await call_next(context)

    def _verify_key(self, api_key: str) -> tuple[bool, str]:
        """
        Verify API key against database.
        Returns (is_valid, key_hash)
        """
        # Get the key prefix to narrow down the search
        prefix = get_key_prefix(api_key)

        # Query only keys matching this prefix (much more efficient)
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key_hash FROM api_keys
            WHERE is_active = 1 AND key_prefix = ?
        """, (prefix,))

        rows = cursor.fetchall()
        conn.close()

        # Check each hash (should be very few or just one)
        for row in rows:
            stored_hash = row['key_hash']
            if verify_key_hash(api_key, stored_hash):
                return True, stored_hash

        return False, ""

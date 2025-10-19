"""
FastMCP middleware for API key authentication.
"""
import logging
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from .key_manager import verify_key_hash, get_key_prefix
from .database import get_db_connection, update_last_used
from .rate_limiter import check_rate_limit

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class APIKeyAuthenticationMiddleware(Middleware):
    """
    Middleware to authenticate API requests using API keys.
    Validates against database using bcrypt.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Authenticate tool calls only (not protocol methods)."""

        logger.info("=" * 80)
        logger.info("AUTH MIDDLEWARE: on_call_tool triggered")
        logger.info(f"Tool name: {context.message.name if hasattr(context, 'message') else 'Unknown'}")

        # Get HTTP request object to access headers
        from fastmcp.server.dependencies import get_http_request

        try:
            logger.debug("Attempting to get HTTP request object...")
            request = get_http_request()
            logger.info(f"[OK] Got HTTP request object: {type(request)}")

            headers = dict(request.headers)
            logger.info(f"[OK] Extracted headers dict with {len(headers)} headers")
            logger.debug(f"All headers: {list(headers.keys())}")

        except Exception as e:
            logger.error(f"[FAIL] Failed to get HTTP request: {type(e).__name__}: {e}")
            raise ToolError("Authentication required - provide API key in Authorization or X-API-Key header")

        # Extract API key from headers
        auth_header = headers.get("authorization", "")
        api_key_header = headers.get("x-api-key", "")

        logger.debug(f"Authorization header present: {bool(auth_header)}")
        logger.debug(f"X-API-Key header present: {bool(api_key_header)}")

        if auth_header:
            logger.debug(f"Authorization header value: {auth_header[:20]}...")
        if api_key_header:
            logger.debug(f"X-API-Key header value: {api_key_header[:20]}...")

        api_key = None

        # Check Authorization header (Bearer token)
        if auth_header.lower().startswith("bearer "):
            api_key = auth_header[7:].strip()
            logger.info("[OK] Extracted API key from Authorization Bearer header")
        # Check X-API-Key header
        elif api_key_header:
            api_key = api_key_header.strip()
            logger.info("[OK] Extracted API key from X-API-Key header")

        # No API key provided
        if not api_key:
            logger.error("[FAIL] No API key found in either header")
            raise ToolError("Missing API key. Provide in Authorization (Bearer) or X-API-Key header")

        logger.debug(f"API key format: {api_key[:18]}...")

        # Validate key format
        if not api_key.startswith("sk_simone_"):
            logger.error(f"[FAIL] Invalid API key format (doesn't start with 'sk_simone_')")
            raise ToolError("Invalid API key format. Must start with 'sk_simone_'")

        logger.info("[OK] API key format valid")

        # Verify key against database
        logger.debug("Verifying API key against database...")
        if not self._verify_key(api_key):
            logger.error("[FAIL] API key verification failed (invalid or revoked)")
            raise ToolError("Invalid or revoked API key")

        logger.info("[OK] API key verified successfully")
        logger.info("[OK] Authentication successful - proceeding with tool call")
        logger.info("=" * 80)

        # Key is valid, proceed
        return await call_next(context)

    def _verify_key(self, api_key: str) -> bool:
        """
        Verify API key against database.
        Returns True if valid, False otherwise.
        """
        logger.debug("_verify_key: Starting verification process")

        # Get the key prefix
        prefix = get_key_prefix(api_key)
        logger.debug(f"_verify_key: Key prefix extracted: {prefix}")

        # Query database
        logger.debug("_verify_key: Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.debug(f"_verify_key: Querying for active key with prefix: {prefix}")
        cursor.execute("""
            SELECT key_hash FROM api_keys
            WHERE is_active = 1 AND key_prefix = ?
        """, (prefix,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning(f"_verify_key: No active key found in database for prefix: {prefix}")
            return False

        logger.debug("_verify_key: Key found in database, verifying hash...")
        stored_hash = row['key_hash']
        logger.debug(f"_verify_key: Stored hash: {stored_hash[:20]}...")

        # Verify with bcrypt
        logger.debug("_verify_key: Running bcrypt verification...")
        if not verify_key_hash(api_key, stored_hash):
            logger.warning("_verify_key: bcrypt verification failed")
            return False

        logger.debug("_verify_key: [OK] bcrypt verification passed")

        # Check rate limit
        logger.debug("_verify_key: Checking rate limit...")
        if not check_rate_limit(stored_hash):
            logger.error("_verify_key: [FAIL] Rate limit exceeded")
            raise ToolError("Rate limit exceeded. Try again later.")

        logger.debug("_verify_key: [OK] Rate limit check passed")

        # Update last used timestamp
        logger.debug("_verify_key: Updating last_used timestamp...")
        try:
            update_last_used(stored_hash)
            logger.debug("_verify_key: [OK] Timestamp updated")
        except Exception as e:
            logger.warning(f"_verify_key: Failed to update timestamp (non-fatal): {e}")
            pass  # Don't fail auth if timestamp update fails

        logger.debug("_verify_key: [OK] All checks passed - key is valid")
        return True

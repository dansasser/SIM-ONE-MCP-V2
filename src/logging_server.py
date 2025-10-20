"""
Wrapper to run FastMCP server with detailed HTTP request logging.
"""
import asyncio
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Mount

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print("=" * 80)
        print("INCOMING HTTP REQUEST")
        print(f"Method: {request.method}")
        print(f"URL: {request.url}")
        print(f"Path: {request.url.path}")
        print(f"\nHEADERS:")
        for name, value in request.headers.items():
            print(f"  {name}: {value}")

        # Read body
        body = await request.body()
        print(f"\nBODY ({len(body)} bytes):")
        if body:
            try:
                print(f"  {body.decode('utf-8')[:1000]}")
            except:
                print(f"  {body[:500]}")
        else:
            print("  (empty)")
        print("=" * 80)

        response = await call_next(request)

        print(f"\nRESPONSE: {response.status_code}")
        print("=" * 80)

        return response

def wrap_fastmcp_with_logging(fastmcp_instance):
    """Wrap FastMCP app with logging middleware."""
    # Get the underlying ASGI app from FastMCP
    original_app = fastmcp_instance._create_asgi_app()

    # Create wrapper with logging
    wrapper = Starlette(debug=True)
    wrapper.add_middleware(LoggingMiddleware)
    wrapper.mount("/", original_app)

    return wrapper

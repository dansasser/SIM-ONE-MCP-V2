"""
Model Context Protocol (MCP) for SIM-ONE-MCP-v2 with SSE Transport

Uses manual SSE transport with HTTP-layer authentication (working architecture).
Based on: https://github.com/zahere-dev/mcp-labs/tree/main/mcp-auth-sse/auth_apikey
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from starlette.applications import Starlette
from starlette.routing import Route, Mount

from fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

# Import authentication
from auth.database import init_database
from auth.database_token_verifier import DatabaseTokenVerifier

# Import tool modules
from tools.esl_emotional_analysis_tutorial import esl_emotional_analysis_tutorial_mcp
from tools.five_laws_validator_tutorial import five_laws_validator_tutorial_mcp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sim-one-mcp-sse")

# Initialize database
logger.info("Initializing database...")
init_database()
logger.info("[OK] Database initialized")

# Create auth verifier instance
logger.info("Creating DatabaseTokenVerifier instance...")
auth_verifier = DatabaseTokenVerifier()
logger.info("[OK] Auth verifier created")

# Initialize the MCP server with tools
mcp = FastMCP(name="SIM-ONE-MCP-v2-SSE")

# Mount tools
mcp.mount(esl_emotional_analysis_tutorial_mcp)
mcp.mount(five_laws_validator_tutorial_mcp)

# Create SSE transport
transport = SseServerTransport("/messages/")


async def check_auth(request: Request):
    """
    Check authentication at HTTP layer BEFORE MCP protocol processing.

    Supports:
    - Authorization: Bearer <api-key>
    - X-API-Key: <api-key>
    """
    auth_header = request.headers.get("authorization", "")
    api_key_header = request.headers.get("x-api-key")

    token = None

    # Extract token from Authorization header
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    # Or from X-API-Key header
    elif api_key_header:
        token = api_key_header

    if not token:
        logger.error("No API key provided in request")
        raise HTTPException(status_code=401, detail="Unauthorized: No API key provided")

    # Verify token using DatabaseTokenVerifier
    access_token = await auth_verifier.verify_token(token)

    if not access_token:
        logger.error("Invalid API key provided")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")

    logger.info(f"Authentication successful for user: {access_token.claims.get('sub')}")
    return True


async def handle_sse(request):
    """
    Handle SSE endpoint - auth check THEN connect to MCP server.
    """
    # Check auth at HTTP layer FIRST
    await check_auth(request=request)

    logger.info("Auth passed, connecting SSE transport...")

    # Prepare bidirectional streams over SSE
    async with transport.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as (in_stream, out_stream):
        logger.info("SSE streams connected, running MCP server...")

        # Run the MCP server: read JSON-RPC from in_stream, write replies to out_stream
        await mcp._mcp_server.run(
            in_stream,
            out_stream,
            mcp._mcp_server.create_initialization_options()
        )


# Build a small Starlette app for the two MCP endpoints
sse_app = Starlette(
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        # Note the trailing slash to avoid 307 redirects
        Mount("/messages/", app=transport.handle_post_message)
    ]
)

# Main FastAPI app
app = FastAPI()
app.mount("/", sse_app)


@app.get("/health")
def health_check():
    return {"status": "ok", "server": "SIM-ONE-MCP-v2-SSE"}


if __name__ == "__main__":
    print("="*80)
    print("SIM-ONE-MCP-v2 Server with SSE Transport + API Key Authentication")
    print("="*80)
    print("\nMCP Endpoint: http://0.0.0.0:8100/sse")
    print("Transport: SSE (Server-Sent Events)")
    print("Authentication: API Key Required")
    print("\nProvide API key in one of these headers:")
    print("  - Authorization: Bearer <your-api-key>")
    print("  - X-API-Key: <your-api-key>")
    print("\nRate Limit: 1000 requests per hour per key")
    print("="*80)
    print()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)

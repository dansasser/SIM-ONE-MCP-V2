"""
Model Context Protocol (MCP) for SIM-ONE-MCP-v2

SIM-ONE is a comprehensive cognitive governance framework that provides emotional analysis and validation tools for AI systems. This implementation combines advanced emotional intelligence capabilities with rigorous Five Laws compliance checking to ensure responsible AI deployment and operation.

This MCP Server contains tools extracted from the following tutorial files:
1. esl_emotional_analysis_tutorial
    - esl_analyze_emotion: Analyze emotional content in text
    - esl_analyze_emotional_progression: Track emotional changes across conversation sequences
    - esl_recommend_response_tone: Generate empathetic response recommendations
    - esl_analyze_text_file: Analyze emotional content from text files
2. five_laws_validator_tutorial
    - five_laws_validate_text: Validate single text against Five Laws with configurable strictness
    - five_laws_batch_validate: Compare multiple texts and identify best performers
    - five_laws_iterative_validate: Iterative refinement workflow with feedback tracking

AUTHENTICATION: Handled by nginx reverse proxy (see auth_service.py)
This server runs without authentication - nginx verifies API keys before forwarding requests.
"""

import logging

from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.middleware import Middleware

# Configure root logger for detailed debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable DEBUG logging for ALL FastMCP components
logging.getLogger("fastmcp").setLevel(logging.DEBUG)
logging.getLogger("fastmcp.server").setLevel(logging.DEBUG)
logging.getLogger("mcp").setLevel(logging.DEBUG)

# HTTP Request Logging Middleware
class HTTPRequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        print("=" * 80)
        print("HTTP REQUEST")
        print("=" * 80)
        print(f"Method: {request.method}")
        print(f"URL: {request.url}")
        print(f"Path: {request.url.path}")
        print(f"Query: {request.url.query}")
        print(f"\nHEADERS:")
        for name, value in request.headers.items():
            print(f"  {name}: {value}")

        # Read the entire body
        body_bytes = await request.body()

        print(f"\nBODY ({len(body_bytes)} bytes):")
        if body_bytes:
            try:
                print(f"  {body_bytes.decode('utf-8')[:2000]}")
            except:
                print(f"  (binary data: {body_bytes[:100]}...)")
        else:
            print("  (empty)")
        print("=" * 80)

        # Replace the request body with our logged body (simpler approach)
        request._body = body_bytes

        response = await call_next(request)

        print(f"RESPONSE: {response.status_code}")
        print("=" * 80)

        return response

# Import tool modules
from tools.esl_emotional_analysis_tutorial import esl_emotional_analysis_tutorial_mcp
from tools.five_laws_validator_tutorial import five_laws_validator_tutorial_mcp

logger.info("=" * 80)
logger.info("SIM-ONE-MCP-V2 SERVER INITIALIZATION (No Auth - Nginx Proxy)")
logger.info("=" * 80)

# Create FastMCP server WITHOUT authentication
# Authentication is handled by nginx proxy before requests reach this server
logger.info("Creating FastMCP server (no auth)...")
mcp = FastMCP(name="SIM-ONE-MCP-v2")
logger.info("[OK] FastMCP server created")

# Mount tools
logger.info("Mounting tools...")
mcp.mount(esl_emotional_analysis_tutorial_mcp)
mcp.mount(five_laws_validator_tutorial_mcp)
logger.info("[OK] Tools mounted")

if __name__ == "__main__":
    print("="*80)
    print("SIM-ONE-MCP-v2 Server (No Auth - Nginx Proxy)")
    print("="*80)
    print("\nMCP Endpoint: http://0.0.0.0:8000/mcp")
    print("Transport: streamable-http")
    print("Authentication: HANDLED BY NGINX PROXY")
    print("\nThis server expects nginx to verify API keys before forwarding requests.")
    print("Direct access to this port should be blocked by firewall.")
    print("="*80)
    print()

    logger.info("Starting server with HTTP request logging...")

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        middleware=[Middleware(HTTPRequestLoggingMiddleware)]
    )

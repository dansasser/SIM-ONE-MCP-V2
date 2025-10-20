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
"""

import logging
from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

# Configure root logger for detailed debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable DEBUG logging for ALL FastMCP components
logging.getLogger("fastmcp").setLevel(logging.DEBUG)
logging.getLogger("fastmcp.server").setLevel(logging.DEBUG)
logging.getLogger("fastmcp.server.auth").setLevel(logging.DEBUG)
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

        # Try to read body
        try:
            body = await request.body()
            print(f"\nBODY ({len(body)} bytes):")
            if body:
                try:
                    print(f"  {body.decode('utf-8')[:1000]}")
                except:
                    print(f"  (binary data: {body[:100]}...)")
            else:
                print("  (empty)")
        except:
            print("\n  (unable to read body)")

        print("=" * 80)

        response = await call_next(request)

        print(f"RESPONSE: {response.status_code}")
        print("=" * 80)

        return response

# Import statements (alphabetical order)
from tools.esl_emotional_analysis_tutorial import esl_emotional_analysis_tutorial_mcp
from tools.five_laws_validator_tutorial import five_laws_validator_tutorial_mcp

# Import authentication
from auth.database import init_database
from auth.fastmcp_auth_middleware import FastMCPAPIKeyAuthMiddleware

logger.info("=" * 80)
logger.info("SIM-ONE-MCP-V2 SERVER INITIALIZATION")
logger.info("=" * 80)

# Initialize database
logger.info("Initializing database...")
init_database()
logger.info("[OK] Database initialized")

# Server definition with middleware-based authentication
logger.info("Creating FastMCP server with middleware-based authentication...")
mcp = FastMCP(
    name="SIM-ONE-MCP-v2"
)
logger.info("[OK] FastMCP server created")
logger.info(f"FastMCP instance: {type(mcp).__name__}")

# Attach API key authentication middleware
logger.info("Adding FastMCPAPIKeyAuthMiddleware for API key verification...")
mcp.add_middleware(FastMCPAPIKeyAuthMiddleware())
logger.info("[OK] Authentication middleware attached")


# Mount tools
mcp.mount(esl_emotional_analysis_tutorial_mcp)
mcp.mount(five_laws_validator_tutorial_mcp)

# Add logging middleware to see all incoming requests
mcp.add_middleware(LoggingMiddleware(
    include_payloads=True,
    max_payload_length=2000
))

if __name__ == "__main__":
    print("="*80)
    print("SIM-ONE-MCP-v2 Server with API Key Authentication")
    print("="*80)
    print("\nMCP Endpoint: http://0.0.0.0:8000/mcp")
    print("Transport: streamable-http")
    print("Authentication: API Key Required")
    print("\nProvide API key in one of these headers:")
    print("  - Authorization: Bearer <your-api-key>")
    print("  - X-API-Key: <your-api-key>")
    print("\nRate Limit: 1000 requests per hour per key")
    print("="*80)
    print()

    logger.info("Starting server with HTTP request logging...")

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        middleware=[Middleware(HTTPRequestLoggingMiddleware)]
    )
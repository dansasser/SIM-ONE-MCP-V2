"""
Model Context Protocol (MCP) for SIM-ONE-MCP-v2 with REST Test Endpoints

This version provides both:
1. MCP endpoint at /mcp (for Claude and other MCP clients)
2. Simple REST endpoints at /test/* (for direct HTTP testing without SSE)

SIM-ONE is a comprehensive cognitive governance framework that provides 
emotional analysis and validation tools for AI systems.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Literal

# Import tool modules
from tools.esl_emotional_analysis_tutorial import esl_emotional_analysis_tutorial_mcp
from tools.five_laws_validator_tutorial import five_laws_validator_tutorial_mcp, validator

# Import authentication
from auth.database import init_database
from auth.middleware import APIKeyAuthMiddleware

# Initialize authentication database
init_database()

# ============================================================================
# Create Main FastAPI App
# ============================================================================

app = FastAPI(
    title="SIM-ONE-MCP-v2 with REST Test Endpoints",
    description="MCP server with additional REST endpoints for testing",
    version="2.0.0"
)

# Add API key authentication middleware
app.add_middleware(APIKeyAuthMiddleware)

# ============================================================================
# Create and Mount MCP Server
# ============================================================================

mcp = FastMCP(name="SIM-ONE-MCP-v2")
mcp.mount(esl_emotional_analysis_tutorial_mcp)
mcp.mount(five_laws_validator_tutorial_mcp)

# Mount MCP server as sub-application
app.mount("/mcp", mcp.http_app(transport="streamable-http"))

# ============================================================================
# REST Test Endpoints (No SSE Required)
# ============================================================================

class ValidateTextRequest(BaseModel):
    text: str
    strictness: Literal["lenient", "moderate", "strict"] = "moderate"

class BatchValidateRequest(BaseModel):
    texts: list[str]
    strictness: Literal["lenient", "moderate", "strict"] = "moderate"

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return JSONResponse({
        "server": "SIM-ONE-MCP-v2",
        "version": "2.0.0",
        "endpoints": {
            "mcp": "/mcp (MCP protocol - requires SSE client like Claude)",
            "test_health": "/test/health",
            "test_tools": "/test/tools",
            "test_validate": "/test/five-laws/validate",
            "test_batch": "/test/five-laws/batch",
            "test_logs": "/test/logs",
            "docs": "/docs (FastAPI auto-generated documentation)"
        },
        "tools_available": 8
    })

@app.get("/test/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "server": "SIM-ONE-MCP-v2",
        "transport": "streamable-http with REST test endpoints",
        "tools_available": 8,
        "mcp_endpoint": "/mcp"
    })

@app.get("/test/tools")
async def list_tools():
    """List all available MCP tools."""
    return JSONResponse({
        "tools": [
            {
                "name": "five_laws_validate_text",
                "description": "Validate single text against Five Laws",
                "category": "Five Laws Validator",
                "test_endpoint": "/test/five-laws/validate"
            },
            {
                "name": "five_laws_batch_validate",
                "description": "Compare multiple texts",
                "category": "Five Laws Validator",
                "test_endpoint": "/test/five-laws/batch"
            },
            {
                "name": "five_laws_iterative_validate",
                "description": "Iterative refinement workflow",
                "category": "Five Laws Validator",
                "test_endpoint": "Use MCP endpoint /mcp"
            },
            {
                "name": "compose_governed_response",
                "description": "Generate governed responses",
                "category": "Five Laws Validator",
                "test_endpoint": "Use MCP endpoint /mcp"
            },
            {
                "name": "esl_analyze_emotion",
                "description": "Analyze emotional content",
                "category": "ESL Emotional Analysis",
                "test_endpoint": "Use MCP endpoint /mcp"
            },
            {
                "name": "esl_analyze_emotional_progression",
                "description": "Track emotional changes",
                "category": "ESL Emotional Analysis",
                "test_endpoint": "Use MCP endpoint /mcp"
            },
            {
                "name": "esl_recommend_response_tone",
                "description": "Generate response recommendations",
                "category": "ESL Emotional Analysis",
                "test_endpoint": "Use MCP endpoint /mcp"
            },
            {
                "name": "esl_analyze_text_file",
                "description": "Analyze text file emotions",
                "category": "ESL Emotional Analysis",
                "test_endpoint": "Use MCP endpoint /mcp"
            }
        ],
        "mcp_endpoint": "/mcp (requires SSE client)",
        "note": "Some tools are only available via MCP endpoint for full functionality"
    })

@app.post("/test/five-laws/validate")
async def test_validate_text(request: ValidateTextRequest):
    """
    Test endpoint for five_laws_validate_text tool.
    
    This endpoint directly calls the validator without going through MCP protocol.
    Useful for quick testing and debugging.

    Example:
        curl -X POST http://localhost:8000/test/five-laws/validate \\
             -H "Content-Type: application/json" \\
             -d '{"text": "Machine learning requires architecture and governance.", "strictness": "moderate"}'
    """
    try:
        result = validator.validate(request.text, strictness=request.strictness)
        return JSONResponse({
            "status": "success",
            "result": result,
            "metadata": {
                "text_length": len(request.text),
                "strictness": request.strictness,
                "note": "Check logs/five_laws_validator.log for detailed logging"
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }, status_code=400)

@app.post("/test/five-laws/batch")
async def test_batch_validate(request: BatchValidateRequest):
    """
    Test endpoint for batch validation of multiple texts.
    
    This endpoint validates multiple texts and returns a summary comparison.

    Example:
        curl -X POST http://localhost:8000/test/five-laws/batch \\
             -H "Content-Type: application/json" \\
             -d '{"texts": ["Text 1 with architecture", "Text 2 with governance"], "strictness": "moderate"}'
    """
    try:
        results = []
        for i, text in enumerate(request.texts, 1):
            result = validator.validate(text, strictness=request.strictness)
            results.append({
                "id": i,
                "text_preview": text[:50] + "..." if len(text) > 50 else text,
                "overall_score": result["scores"]["overall_compliance"],
                "status": result["pass_fail_status"],
                "violations": len(result.get("violations", [])),
                "recommendations": len(result.get("recommendations", [])),
                "scores": result["scores"]
            })

        # Calculate summary statistics
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        conditional = sum(1 for r in results if r["status"] == "CONDITIONAL")
        avg_score = sum(r["overall_score"] for r in results) / len(results) if results else 0

        return JSONResponse({
            "status": "success",
            "batch_size": len(request.texts),
            "results": results,
            "summary": {
                "passed": passed,
                "failed": failed,
                "conditional": conditional,
                "average_score": round(avg_score, 2),
                "best_score": max((r["overall_score"] for r in results), default=0),
                "worst_score": min((r["overall_score"] for r in results), default=0)
            },
            "metadata": {
                "strictness": request.strictness,
                "note": "Check logs/five_laws_validator.log for detailed logging"
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }, status_code=400)

@app.get("/test/logs")
async def view_recent_logs():
    """View last 20 lines from each log file."""
    import os
    from pathlib import Path
    from collections import deque

    # Feature flag: disabled by default for security
    if os.getenv("SIMONE_ENABLE_LOGS_VIEW", "0") != "1":
        return JSONResponse({
            "status": "error",
            "message": "Logs view endpoint is disabled. Set SIMONE_ENABLE_LOGS_VIEW=1 to enable."
        }, status_code=404)

    PROJECT_ROOT = Path(__file__).parent.parent
    LOG_DIR = PROJECT_ROOT / "logs"

    if not LOG_DIR.exists():
        return JSONResponse({
            "status": "error",
            "message": "Log directory not found",
            "log_directory": str(LOG_DIR)
        })

    logs = {}
    for log_file in LOG_DIR.glob("*.log"):
        try:
            # Efficient tail: keep only last N lines without loading entire file
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                tail = list(deque(f, maxlen=20))
                logs[log_file.name] = {
                    "recent_lines": tail
                }
        except (OSError, UnicodeDecodeError) as e:
            logs[log_file.name] = {
                "error": f"Error reading log: {e}"
            }

    return JSONResponse({
        "status": "success",
        "logs": logs,
        "log_directory": str(LOG_DIR),
        "note": "Showing last 20 lines from each log file"
    })

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("SIM-ONE-MCP-v2 Server with REST Test Endpoints")
    print("=" * 80)
    print("\n📡 MCP Endpoint (for Claude and MCP clients):")
    print("   http://localhost:8000/mcp")
    print("   - Requires SSE-capable MCP client")
    print("   - All 8 tools available")
    print("\n🧪 REST Test Endpoints (for direct HTTP testing):")
    print("   GET  http://localhost:8000/")
    print("   GET  http://localhost:8000/test/health")
    print("   GET  http://localhost:8000/test/tools")
    print("   POST http://localhost:8000/test/five-laws/validate")
    print("   POST http://localhost:8000/test/five-laws/batch")
    print("   GET  http://localhost:8000/test/logs")
    print("\n📚 Documentation:")
    print("   http://localhost:8000/docs (FastAPI auto-generated)")
    print("\n📝 Logs:")
    print("   logs/five_laws_validator.log")
    print("   logs/governed_response_composer.log")
    print("=" * 80)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


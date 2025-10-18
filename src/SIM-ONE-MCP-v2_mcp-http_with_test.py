"""
Model Context Protocol (MCP) for SIM-ONE-MCP-v2 with Test Endpoints

This version adds simple REST endpoints for testing tool calls without SSE complexity.

SIM-ONE is a comprehensive cognitive governance framework that provides emotional analysis and validation tools for AI systems.
"""

from fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Literal

# Import statements
from tools.esl_emotional_analysis_tutorial import esl_emotional_analysis_tutorial_mcp
from tools.five_laws_validator_tutorial import five_laws_validator_tutorial_mcp, validator

# Server definition and mounting
mcp = FastMCP(name="SIM-ONE-MCP-v2")
mcp.mount(esl_emotional_analysis_tutorial_mcp)
mcp.mount(five_laws_validator_tutorial_mcp)

# Get the underlying FastAPI app
app = mcp.get_app()

# ============================================================================
# Test REST Endpoints (No SSE Required)
# ============================================================================

class ValidateTextRequest(BaseModel):
    text: str
    strictness: Literal["lenient", "moderate", "strict"] = "moderate"

class BatchValidateRequest(BaseModel):
    texts: list[str]
    strictness: Literal["lenient", "moderate", "strict"] = "moderate"

@app.get("/test/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "server": "SIM-ONE-MCP-v2",
        "transport": "streamable-http with REST test endpoints",
        "tools_available": 7
    })

@app.get("/test/tools")
async def list_tools():
    """List all available MCP tools."""
    return JSONResponse({
        "tools": [
            {
                "name": "five_laws_validate_text",
                "description": "Validate single text against Five Laws",
                "endpoint": "/test/five-laws/validate"
            },
            {
                "name": "five_laws_batch_validate",
                "description": "Compare multiple texts",
                "endpoint": "/test/five-laws/batch"
            },
            {
                "name": "five_laws_iterative_validate",
                "description": "Iterative refinement workflow",
                "endpoint": "/test/five-laws/iterative"
            },
            {
                "name": "esl_analyze_emotion",
                "description": "Analyze emotional content",
                "note": "Use MCP endpoint /mcp for full access"
            },
            {
                "name": "esl_analyze_emotional_progression",
                "description": "Track emotional changes",
                "note": "Use MCP endpoint /mcp for full access"
            },
            {
                "name": "esl_recommend_response_tone",
                "description": "Generate response recommendations",
                "note": "Use MCP endpoint /mcp for full access"
            },
            {
                "name": "compose_governed_response",
                "description": "Generate governed responses",
                "note": "Use MCP endpoint /mcp for full access"
            }
        ],
        "mcp_endpoint": "/mcp (requires SSE client)"
    })

@app.post("/test/five-laws/validate")
async def test_validate_text(request: ValidateTextRequest):
    """
    Test endpoint for five_laws_validate_text tool.

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
            "logging": {
                "note": "Check logs/five_laws_validator.log for detailed logging",
                "format": "pipe-delimited key=value"
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "type": type(e).__name__
        }, status_code=400)

@app.post("/test/five-laws/batch")
async def test_batch_validate(request: BatchValidateRequest):
    """
    Test endpoint for five_laws_batch_validate tool.

    Example:
        curl -X POST http://localhost:8000/test/five-laws/batch \\
             -H "Content-Type: application/json" \\
             -d '{"texts": ["Text 1", "Text 2"], "strictness": "moderate"}'
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
                "recommendations": len(result.get("recommendations", []))
            })

        return JSONResponse({
            "status": "success",
            "batch_size": len(request.texts),
            "results": results,
            "summary": {
                "passed": sum(1 for r in results if r["status"] == "PASS"),
                "failed": sum(1 for r in results if r["status"] == "FAIL"),
                "average_score": sum(r["overall_score"] for r in results) / len(results)
            },
            "logging": {
                "note": "Check logs/five_laws_validator.log for detailed logging",
                "format": "pipe-delimited key=value"
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "type": type(e).__name__
        }, status_code=400)

@app.get("/test/logs")
async def view_recent_logs():
    """View last 10 lines from each log file."""
    import os
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).parent.parent
    LOG_DIR = PROJECT_ROOT / "logs"

    logs = {}
    for log_file in LOG_DIR.glob("*.log"):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logs[log_file.name] = lines[-10:] if len(lines) > 10 else lines
        except Exception as e:
            logs[log_file.name] = [f"Error reading log: {e}"]

    return JSONResponse({
        "logs": logs,
        "log_directory": str(LOG_DIR),
        "note": "Showing last 10 lines from each log file"
    })

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SIM-ONE MCP Server with Test Endpoints")
    print("=" * 60)
    print("\nMCP Endpoint:")
    print("  http://localhost:8000/mcp (requires SSE client)")
    print("\nTest Endpoints (simple REST):")
    print("  GET  http://localhost:8000/test/health")
    print("  GET  http://localhost:8000/test/tools")
    print("  POST http://localhost:8000/test/five-laws/validate")
    print("  POST http://localhost:8000/test/five-laws/batch")
    print("  GET  http://localhost:8000/test/logs")
    print("\nDocumentation:")
    print("  http://localhost:8000/docs (FastAPI auto-docs)")
    print("\nLogs:")
    print("  logs/five_laws_validator.log")
    print("  logs/governed_response_composer.log")
    print("=" * 60)
    print()

    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

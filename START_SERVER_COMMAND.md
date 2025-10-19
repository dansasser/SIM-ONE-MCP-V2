# SERVER START COMMAND - DO NOT FORGET

## THE ONLY COMMAND TO START THE SERVER

```bash
uv run --python "C:\\Users\\admin\\OneDrive\\Desktop\\Paper2Agent\\sim-one-venv\\Scripts\\python.exe" --with fastmcp "C:\\Claude\\SIM-ONE-MCP-v2\\src\\SIM-ONE-MCP-v2_mcp-http.py"
```

## NEVER USE THESE (WRONG):
- ❌ `fastmcp run src.SIM-ONE-MCP-v2_mcp-http:mcp --port 8000`
- ❌ `python src/SIM-ONE-MCP-v2_mcp-http.py`
- ❌ Any other variation

## THE CORRECT COMMAND AGAIN:
```bash
uv run --python "C:\\Users\\admin\\OneDrive\\Desktop\\Paper2Agent\\sim-one-venv\\Scripts\\python.exe" --with fastmcp "C:\\Claude\\SIM-ONE-MCP-v2\\src\\SIM-ONE-MCP-v2_mcp-http.py"
```

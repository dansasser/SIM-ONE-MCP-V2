# Full MCP session test - Initialize, then call tool

$baseUrl = "http://127.0.0.1:8000/mcp"
$apiKey = "sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk"

Write-Host "Step 1: Initialize session..." -ForegroundColor Cyan

$initHeaders = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $apiKey"
    "accept" = "text/event-stream, application/json"
}

$initBody = '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{"elicitation":{}},"clientInfo":{"name":"powershell-test","version":"1.0.0"}}}'

try {
    $initResponse = Invoke-WebRequest -Uri $baseUrl -Method Post -Headers $initHeaders -Body $initBody -UseBasicParsing

    # Extract session ID from Set-Cookie header
    $sessionId = $null
    foreach ($header in $initResponse.Headers.GetEnumerator()) {
        if ($header.Key -eq "mcp-session-id") {
            $sessionId = $header.Value[0]
            break
        }
    }

    if (-not $sessionId) {
        Write-Host "ERROR: No session ID returned from initialize" -ForegroundColor Red
        exit 1
    }

    Write-Host "SUCCESS: Session ID = $sessionId" -ForegroundColor Green

    Write-Host "`nStep 2: Call tool with session..." -ForegroundColor Cyan

    $toolHeaders = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $apiKey"
        "mcp-session-id" = $sessionId
        "accept" = "text/event-stream, application/json"
    }

    $toolBody = '{"jsonrpc":"2.0","id":999,"method":"tools/call","params":{"name":"five_laws_validate_text","arguments":{"text":"the world will end in 2030"}}}'

    $toolResponse = Invoke-WebRequest -Uri $baseUrl -Method Post -Headers $toolHeaders -Body $toolBody -UseBasicParsing

    Write-Host "SUCCESS: Tool call status = $($toolResponse.StatusCode)" -ForegroundColor Green
    Write-Host "`nResponse:" -ForegroundColor Yellow
    Write-Host $toolResponse.Content

} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.Exception -ForegroundColor Red
}

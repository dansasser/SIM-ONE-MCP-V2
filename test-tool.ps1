$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer sk_simone_uiDejaAs6WFL3AMS3PWjLOA3Rn7ZZqdk"
    "mcp-session-id" = "9305196a98284889ace5ccb55d57a3ce"
    "accept" = "text/event-stream, application/json"
}

$body = '{"jsonrpc":"2.0","id":999,"method":"tools/call","params":{"name":"five_laws_validate_text","arguments":{"text":"the world will end in 2030"}}}'

Invoke-RestMethod -Uri "http://127.0.0.1:8000/mcp" -Method Post -Headers $headers -Body $body

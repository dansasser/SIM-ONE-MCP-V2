# API Key Authentication

## Overview

SIM-ONE-MCP-v2 now requires API key authentication for all requests to the MCP server. This ensures secure access control and usage tracking.

## Features

- ✅ **API Key Management** - Create, list, revoke keys via CLI
- ✅ **User Tracking** - Keys are associated with user emails
- ✅ **Rate Limiting** - 1000 requests per hour per key
- ✅ **Secure Storage** - Keys are hashed with bcrypt
- ✅ **Multiple Keys** - Users can have multiple active keys
- ✅ **Usage Tracking** - Last used timestamp is tracked

---

## Quick Start

### 1. Create an API Key

```bash
cd /path/to/SIM-ONE-MCP-V2
python3 scripts/manage_api_keys.py create --email your@email.com --description "My key"
```

**Save the API key shown - it will not be displayed again!**

### 2. Start the Server

```bash
cd src
python3 SIM-ONE-MCP-v2_mcp-http.py
```

### 3. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add your API key:

```json
{
  "mcpServers": {
    "sim-one": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer sk_simone_your_key_here"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

Close and reopen Claude Desktop to apply the configuration.

---

## API Key Management

### Create a Key

```bash
python3 scripts/manage_api_keys.py create --email user@example.com --description "Production key"
```

**Interactive mode:**
```bash
bash scripts/create_api_key.sh
```

### List Keys

```bash
# List all keys
python3 scripts/manage_api_keys.py list

# List keys for specific user
python3 scripts/manage_api_keys.py list --email user@example.com
```

### Show Key Details

```bash
python3 scripts/manage_api_keys.py info --prefix sk_simone_abc12345
```

### Revoke a Key

```bash
# With confirmation
python3 scripts/manage_api_keys.py revoke --prefix sk_simone_abc12345

# Skip confirmation
python3 scripts/manage_api_keys.py revoke --prefix sk_simone_abc12345 --yes
```

---

## Using API Keys

### Header Formats

You can provide the API key in two ways:

**Option 1: Authorization Bearer Token (Recommended)**
```
Authorization: Bearer sk_simone_your_key_here
```

**Option 2: X-API-Key Header**
```
X-API-Key: sk_simone_your_key_here
```

### With Claude Desktop

```json
{
  "mcpServers": {
    "sim-one": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer sk_simone_your_key_here"
      }
    }
  }
}
```

### With curl

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_simone_your_key_here" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### With Python (FastMCP Client)

```python
from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport

transport = StreamableHttpTransport(
    url="http://localhost:8000/mcp",
    headers={"Authorization": "Bearer sk_simone_your_key_here"}
)

client = Client(transport)

async with client:
    tools = await client.list_tools()
    print(f"Found {len(tools)} tools")
```

---

## Rate Limiting

- **Limit:** 1000 requests per hour per API key
- **Window:** Rolling 1-hour window
- **Response:** HTTP 429 when limit exceeded

### Rate Limit Response

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Rate limit: 1000 requests per hour"
}
```

---

## Error Responses

### Missing API Key

**Status:** 401 Unauthorized

```json
{
  "error": "Missing API key",
  "message": "Provide API key in Authorization header (Bearer token) or X-API-Key header"
}
```

### Invalid API Key

**Status:** 401 Unauthorized

```json
{
  "error": "Invalid API key",
  "message": "The provided API key is invalid or has been revoked"
}
```

### Invalid Format

**Status:** 401 Unauthorized

```json
{
  "error": "Invalid API key format",
  "message": "API key must start with 'sk_simone_'"
}
```

### Rate Limit Exceeded

**Status:** 429 Too Many Requests

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Rate limit: 1000 requests per hour"
}
```

---

## Security Best Practices

### Key Storage

- ✅ **Never commit keys to version control**
- ✅ **Store keys in environment variables or secure vaults**
- ✅ **Rotate keys periodically**
- ✅ **Revoke unused or compromised keys immediately**

### Key Format

- Keys start with `sk_simone_`
- 32 random alphanumeric characters
- Total length: 42 characters
- Example: `sk_simone_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6`

### Database Security

- Keys are hashed with bcrypt before storage
- Only key prefixes (first 18 chars) are stored for identification
- Database file: `data/api_keys.db`
- Set proper file permissions: `chmod 600 data/api_keys.db`

### Network Security

- ⚠️ **Use HTTPS in production**
- ⚠️ **Do not use HTTP for production deployments**
- ⚠️ **API keys sent over HTTP can be intercepted**

### Production Deployment

For production use:

1. **Use HTTPS** - Set up reverse proxy (nginx, Caddy) with SSL/TLS
2. **Restrict Host** - Change `host="0.0.0.0"` to `host="127.0.0.1"` if local only
3. **Firewall Rules** - Restrict access to port 8000
4. **Monitor Usage** - Track API key usage and revoke suspicious keys
5. **Backup Database** - Regularly backup `data/api_keys.db`

---

## Database

### Location

```
data/api_keys.db
```

### Schema

**Table: api_keys**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| key_hash | TEXT | Bcrypt hash of the API key |
| key_prefix | TEXT | First 18 characters for identification |
| user_email | TEXT | Owner's email address |
| description | TEXT | Optional description |
| created_at | TIMESTAMP | When the key was created |
| last_used_at | TIMESTAMP | Last time the key was used |
| is_active | BOOLEAN | Whether the key is active (not revoked) |
| expires_at | TIMESTAMP | Expiration date (currently unused) |

### Backup

```bash
# Backup database
cp data/api_keys.db data/api_keys.db.backup

# Restore from backup
cp data/api_keys.db.backup data/api_keys.db
```

---

## Troubleshooting

### "Missing API key" Error

**Problem:** No API key provided in request

**Solution:** Add API key to `Authorization` or `X-API-Key` header

### "Invalid API key" Error

**Problem:** Key is wrong, revoked, or doesn't exist

**Solutions:**
- Check that you copied the full key correctly
- Verify key is active: `python3 scripts/manage_api_keys.py info --prefix <prefix>`
- Create a new key if needed

### "Rate limit exceeded" Error

**Problem:** Too many requests in the last hour

**Solutions:**
- Wait for the rate limit window to reset
- Create additional API keys for different services
- Contact administrator to increase rate limit

### Claude Desktop Not Connecting

**Problem:** Claude can't connect to MCP server

**Solutions:**
1. Check server is running: `ps aux | grep SIM-ONE-MCP-v2_mcp-http.py`
2. Verify config file syntax is correct (valid JSON)
3. Check API key is correct in config
4. Restart Claude Desktop after config changes
5. Check server logs for errors

### Database Locked Error

**Problem:** SQLite database is locked

**Solutions:**
- Close any other processes accessing the database
- Restart the server
- Check file permissions on `data/api_keys.db`

---

## File Structure

```
SIM-ONE-MCP-V2/
├── src/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── database.py          # Database operations
│   │   ├── key_manager.py       # Key generation and validation
│   │   ├── middleware.py        # Authentication middleware
│   │   └── rate_limiter.py      # Rate limiting logic
│   └── SIM-ONE-MCP-v2_mcp-http.py  # Main server (with auth)
├── scripts/
│   ├── manage_api_keys.py       # CLI management tool
│   └── create_api_key.sh        # Interactive key creation
├── data/
│   └── api_keys.db              # SQLite database
└── docs/
    └── API_KEY_AUTHENTICATION.md  # This file
```

---

## FAQ

### Q: Can I disable authentication for local development?

**A:** No, authentication is always required. Create a development key for local use.

### Q: Do API keys expire?

**A:** No, keys do not expire automatically. Revoke keys manually when no longer needed.

### Q: Can I have multiple keys for the same email?

**A:** Yes, users can have multiple active keys with different descriptions.

### Q: What happens if I lose my API key?

**A:** Create a new key and revoke the old one. Keys cannot be recovered once lost.

### Q: Can I change the rate limit?

**A:** Yes, edit `src/auth/rate_limiter.py` and change `max_requests` parameter.

### Q: How do I migrate existing deployments?

**A:** 
1. Create API keys for all users
2. Update client configurations with new keys
3. Deploy the updated server
4. Test all clients

### Q: Is the database encrypted?

**A:** Keys are hashed with bcrypt. The database file itself is not encrypted. Use filesystem encryption if needed.

---

## Support

For issues or questions:
- Check server logs: `tail -f /tmp/mcp-auth-server.log`
- Review this documentation
- Check GitHub issues: https://github.com/dansasser/SIM-ONE-MCP-V2


#!/bin/bash
#
# Interactive script to create API keys for SIM-ONE-MCP-v2
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGE_SCRIPT="$SCRIPT_DIR/manage_api_keys.py"

echo "================================================================================"
echo "SIM-ONE-MCP-v2 API Key Generator"
echo "================================================================================"
echo ""

# Prompt for email
read -p "Enter user email address: " EMAIL

if [ -z "$EMAIL" ]; then
    echo "Error: Email is required"
    exit 1
fi

# Prompt for description (optional)
read -p "Enter description (optional, press Enter to skip): " DESCRIPTION

echo ""
echo "Creating API key..."
echo ""

# Create the key
if [ -z "$DESCRIPTION" ]; then
    python3 "$MANAGE_SCRIPT" create --email "$EMAIL"
else
    python3 "$MANAGE_SCRIPT" create --email "$EMAIL" --description "$DESCRIPTION"
fi


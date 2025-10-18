#!/usr/bin/env python3
"""
CLI tool for managing API keys for SIM-ONE-MCP-v2.
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

from auth.database import init_database, get_key_by_prefix
from auth.key_manager import create_api_key, list_api_keys, revoke_api_key


def cmd_create(args):
    """Create a new API key."""
    print("Creating new API key...")
    print(f"  User: {args.email}")
    if args.description:
        print(f"  Description: {args.description}")
    print()
    
    # Create key
    api_key, key_id = create_api_key(args.email, args.description)
    
    print("✓ API Key created successfully!")
    print()
    print("=" * 80)
    print("IMPORTANT: Save this API key now. It will not be shown again!")
    print("=" * 80)
    print()
    print(f"API Key: {api_key}")
    print()
    print(f"Key ID: {key_id}")
    print(f"Prefix: {api_key[:18]}")
    print(f"User: {args.email}")
    print()
    print("Use this key in your MCP client configuration:")
    print()
    print('  "headers": {')
    print(f'    "Authorization": "Bearer {api_key}"')
    print('  }')
    print()
    print("=" * 80)


def cmd_list(args):
    """List API keys."""
    if args.email:
        print(f"API keys for {args.email}:")
        keys = list_api_keys(args.email)
    else:
        print("All API keys:")
        keys = list_api_keys()
    
    if not keys:
        print("  No keys found.")
        return
    
    print()
    print(f"{'ID':<6} {'Prefix':<20} {'Email':<30} {'Active':<8} {'Created':<20} {'Last Used':<20}")
    print("-" * 120)
    
    for key in keys:
        key_id = key['id']
        prefix = key['key_prefix']
        email = key['user_email']
        active = "Yes" if key['is_active'] else "No"
        created = key['created_at']
        last_used = key['last_used_at'] if key['last_used_at'] else "Never"
        
        print(f"{key_id:<6} {prefix:<20} {email:<30} {active:<8} {created:<20} {last_used:<20}")
    
    print()
    print(f"Total: {len(keys)} key(s)")


def cmd_revoke(args):
    """Revoke an API key."""
    print(f"Revoking API key with prefix: {args.prefix}")
    
    # Check if key exists
    key_info = get_key_by_prefix(args.prefix)
    if not key_info:
        print(f"✗ Error: No key found with prefix '{args.prefix}'")
        sys.exit(1)
    
    # Show key info
    print()
    print("Key details:")
    print(f"  ID: {key_info['id']}")
    print(f"  Prefix: {key_info['key_prefix']}")
    print(f"  User: {key_info['user_email']}")
    print(f"  Active: {'Yes' if key_info['is_active'] else 'No'}")
    print()
    
    if not key_info['is_active']:
        print("✗ Key is already revoked.")
        return
    
    # Confirm
    if not args.yes:
        response = input("Are you sure you want to revoke this key? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
    
    # Revoke
    success = revoke_api_key(args.prefix)
    
    if success:
        print("✓ API key revoked successfully.")
    else:
        print("✗ Error revoking key.")
        sys.exit(1)


def cmd_info(args):
    """Show detailed information about an API key."""
    key_info = get_key_by_prefix(args.prefix)
    
    if not key_info:
        print(f"✗ Error: No key found with prefix '{args.prefix}'")
        sys.exit(1)
    
    print()
    print("API Key Information")
    print("=" * 60)
    print(f"ID:          {key_info['id']}")
    print(f"Prefix:      {key_info['key_prefix']}")
    print(f"User Email:  {key_info['user_email']}")
    print(f"Description: {key_info.get('description', 'N/A')}")
    print(f"Active:      {'Yes' if key_info['is_active'] else 'No (Revoked)'}")
    print(f"Created:     {key_info['created_at']}")
    print(f"Last Used:   {key_info['last_used_at'] if key_info['last_used_at'] else 'Never'}")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage API keys for SIM-ONE-MCP-v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new API key
  %(prog)s create --email user@example.com --description "Production key"
  
  # List all keys
  %(prog)s list
  
  # List keys for specific user
  %(prog)s list --email user@example.com
  
  # Show key details
  %(prog)s info --prefix sk_simone_abc12345
  
  # Revoke a key
  %(prog)s revoke --prefix sk_simone_abc12345
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new API key')
    create_parser.add_argument('--email', required=True, help='User email address')
    create_parser.add_argument('--description', help='Optional description for the key')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List API keys')
    list_parser.add_argument('--email', help='Filter by user email')
    
    # Revoke command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke an API key')
    revoke_parser.add_argument('--prefix', required=True, help='Key prefix (e.g., sk_simone_abc12345)')
    revoke_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show detailed key information')
    info_parser.add_argument('--prefix', required=True, help='Key prefix (e.g., sk_simone_abc12345)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize database
    init_database()
    
    # Execute command
    if args.command == 'create':
        cmd_create(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'revoke':
        cmd_revoke(args)
    elif args.command == 'info':
        cmd_info(args)


if __name__ == '__main__':
    main()


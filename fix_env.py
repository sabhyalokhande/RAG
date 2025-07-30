#!/usr/bin/env python3
"""
Fix .env file with correct Azure deployment names
"""
import os
from pathlib import Path

def fix_env():
    """Fix the .env file with correct deployment names."""
    print("🔧 Fixing .env file with correct deployment names")
    print("=" * 50)
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return
    
    # Read current .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    print("📋 Current .env content:")
    print(content)
    
    # Fix the deployment names
    fixed_content = content.replace(
        "AZURE_DEPLOYMENT_EMBEDDING=text-embedding-3-small",
        "AZURE_DEPLOYMENT_EMBEDDING=text-embedding-ada-002"
    )
    
    # Also update completion model to match what you have
    fixed_content = fixed_content.replace(
        "AZURE_DEPLOYMENT_COMPLETION=gpt-35-turbo",
        "AZURE_DEPLOYMENT_COMPLETION=gpt-35-turbo"
    )
    
    # Write back the fixed content
    with open(env_file, 'w') as f:
        f.write(fixed_content)
    
    print("\n✅ .env file updated!")
    print("📋 Changes made:")
    print("  - AZURE_DEPLOYMENT_EMBEDDING: text-embedding-3-small → text-embedding-ada-002")
    print("  - AZURE_DEPLOYMENT_COMPLETION: gpt-35-turbo (kept as is)")
    
    print("\n🔧 Next steps:")
    print("1. Restart the Flask server")
    print("2. Test the system")

if __name__ == "__main__":
    fix_env() 
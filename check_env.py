#!/usr/bin/env python3
"""
Check environment variables in Flask app context
"""
import os
from app import create_app

def check_env():
    """Check environment variables in Flask app context."""
    print("🔍 Checking Environment Variables")
    print("=" * 50)
    
    # Create Flask app to get the context
    app = create_app()
    
    with app.app_context():
        print("📋 Environment Variables:")
        print(f"  AZURE_OPENAI_API_KEY: {'✅ Set' if os.environ.get('AZURE_OPENAI_API_KEY') else '❌ Not set'}")
        print(f"  AZURE_OPENAI_ENDPOINT: {'✅ Set' if os.environ.get('AZURE_OPENAI_ENDPOINT') else '❌ Not set'}")
        print(f"  AZURE_DEPLOYMENT_EMBEDDING: {os.environ.get('AZURE_DEPLOYMENT_EMBEDDING', 'text-embedding-ada-002')}")
        print(f"  AZURE_DEPLOYMENT_COMPLETION: {os.environ.get('AZURE_DEPLOYMENT_COMPLETION', 'gpt-4')}")
        
        # Check if we can import the config
        from config import Config
        print(f"\n📋 Config Values:")
        print(f"  AZURE_OPENAI_API_KEY: {'✅ Set' if Config.AZURE_OPENAI_API_KEY else '❌ Not set'}")
        print(f"  AZURE_OPENAI_ENDPOINT: {'✅ Set' if Config.AZURE_OPENAI_ENDPOINT else '❌ Not set'}")
        print(f"  AZURE_DEPLOYMENT_EMBEDDING: {Config.AZURE_DEPLOYMENT_EMBEDDING}")
        print(f"  AZURE_DEPLOYMENT_COMPLETION: {Config.AZURE_DEPLOYMENT_COMPLETION}")

if __name__ == "__main__":
    check_env() 
#!/usr/bin/env python3
"""
Setup environment variables for Azure OpenAI
"""
import os
from pathlib import Path

def setup_env():
    """Help set up environment variables."""
    print("🔧 Azure OpenAI Environment Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file found!")
        print("📋 Current .env contents:")
        with open(env_file, 'r') as f:
            print(f.read())
    else:
        print("❌ .env file not found!")
        print("\n📝 Creating .env file template...")
        
        # Create .env file template
        env_content = """# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here

# Deployment Names (these are already correct)
AZURE_DEPLOYMENT_EMBEDDING=text-embedding-ada-002
AZURE_DEPLOYMENT_COMPLETION=gpt-4

# Other Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created!")
        print("\n🔧 Next steps:")
        print("1. Edit the .env file and replace:")
        print("   - your_api_key_here with your Azure OpenAI API key")
        print("   - your_endpoint_here with your Azure OpenAI endpoint")
        print("2. Restart the Flask server")
    
    print("\n📋 Current Environment Variables:")
    print(f"  AZURE_OPENAI_API_KEY: {'✅ Set' if os.environ.get('AZURE_OPENAI_API_KEY') else '❌ Not set'}")
    print(f"  AZURE_OPENAI_ENDPOINT: {'✅ Set' if os.environ.get('AZURE_OPENAI_ENDPOINT') else '❌ Not set'}")
    print(f"  AZURE_DEPLOYMENT_EMBEDDING: {os.environ.get('AZURE_DEPLOYMENT_EMBEDDING', 'text-embedding-ada-002')}")
    print(f"  AZURE_DEPLOYMENT_COMPLETION: {os.environ.get('AZURE_DEPLOYMENT_COMPLETION', 'gpt-4')}")
    
    if not os.environ.get('AZURE_OPENAI_API_KEY') or not os.environ.get('AZURE_OPENAI_ENDPOINT'):
        print("\n❌ Environment variables not set!")
        print("Please set them in the .env file and restart the server.")

if __name__ == "__main__":
    setup_env() 
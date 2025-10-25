#!/usr/bin/env python3
"""
Setup script to create API keys configuration file
"""

import os
import json
import sys
from datetime import datetime

def setup_api_keys():
    """Create API keys configuration file"""
    
    # Determine config path (same logic as api_server.py)
    CONFIG_PATH = os.getenv('WINDOWS_USE_CONFIG_PATH', os.path.join(os.getcwd(), 'config'))
    
    # Create config directory if it doesn't exist
    os.makedirs(CONFIG_PATH, exist_ok=True)
    
    config_file = os.path.join(CONFIG_PATH, "api_keys.json")
    
    print(f"🔧 Setting up API keys configuration...")
    print(f"📁 Config directory: {CONFIG_PATH}")
    print(f"📄 Config file: {config_file}")
    
    # Check if file already exists
    if os.path.exists(config_file):
        print(f"⚠️  Config file already exists: {config_file}")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Setup cancelled")
            return
    
    # Get API keys from user
    print("\n🔑 Please enter your API keys (press Enter to skip):")
    
    google_key = input("Google API Key: ").strip()
    elevenlabs_key = input("ElevenLabs API Key (optional): ").strip()
    deepgram_key = input("Deepgram API Key (optional): ").strip()
    
    # Create config data
    config_data = {
        "google_api_key": google_key,
        "elevenlabs_api_key": elevenlabs_key,
        "deepgram_api_key": deepgram_key,
        "last_updated": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    try:
        # Write config file
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ API keys configuration saved to: {config_file}")
        print("🚀 You can now start the Electron app!")
        
        # Show what was saved
        print("\n📋 Configuration summary:")
        print(f"  Google API Key: {'✅ Set' if google_key else '❌ Not set'}")
        print(f"  ElevenLabs API Key: {'✅ Set' if elevenlabs_key else '❌ Not set'}")
        print(f"  Deepgram API Key: {'✅ Set' if deepgram_key else '❌ Not set'}")
        
        if not google_key:
            print("\n⚠️  WARNING: Google API key is required for the agent to work!")
            print("   You can set it later in the settings page of the app.")
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_api_keys()



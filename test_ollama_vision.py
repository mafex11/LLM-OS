#!/usr/bin/env python3
"""
Quick test to verify Ollama gemma3:latest supports vision.
Run this before using the agent to ensure your model is working.
"""

import requests
import base64
from PIL import Image, ImageDraw
import io

def create_test_image():
    """Create a simple test image with text"""
    img = Image.new('RGB', (200, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "TEST IMAGE", fill='black')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_ollama_vision():
    """Test if Ollama gemma3:latest can handle images"""
    print("🧪 Testing Ollama vision support...")
    
    # Create test image
    test_image_b64 = create_test_image()
    
    # Prepare request
    payload = {
        "model": "gemma3:latest",
        "messages": [
            {
                "role": "user",
                "content": "What text do you see in this image?",
                "images": [test_image_b64]
            }
        ],
        "stream": False
    }
    
    try:
        print("📡 Sending test request to Ollama...")
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("message", {}).get("content", "")
            print(f"✅ Success! Ollama responded: {content}")
            
            if "test" in content.lower():
                print("🎉 Vision is working - model can see the test image!")
            else:
                print("⚠️  Model responded but may not see image correctly")
                
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Make sure 'ollama serve' is running.")
    except requests.exceptions.Timeout:
        print("⏰ Request timed out. Model may be processing slowly.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ollama_vision()

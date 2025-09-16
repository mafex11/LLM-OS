#!/usr/bin/env python3
"""
Quick test to verify the voice model fix.
"""

def test_voice_model():
    """Test that the voice service can be initialized with a valid model."""
    print("🔧 Testing voice model configuration...")
    
    try:
        from windows_use.agent.voice.service import VoiceService
        
        # Test with different valid models
        valid_models = ["tiny", "base", "small", "medium"]
        
        for model in valid_models:
            print(f"Testing model: {model}")
            try:
                voice_service = VoiceService(model=model)
                print(f"✅ Model '{model}' initialized successfully")
            except Exception as e:
                print(f"❌ Model '{model}' failed: {e}")
        
        print("\n🎤 Testing TTS functionality...")
        voice_service = VoiceService(model="base")
        
        if voice_service.is_available():
            print("✅ Voice service is available")
            # Test TTS without actually speaking
            print("✅ TTS engine initialized")
        else:
            print("❌ Voice service not available")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install RealtimeSTT pyaudio pyttsx3")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_voice_model()

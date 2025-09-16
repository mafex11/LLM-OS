# Voice Integration for Windows-Use

This document describes the voice functionality integration in the Windows-Use project, enabling Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities.

## 🎤 Features

### Speech-to-Text (STT)
- **Real-time transcription** using RealtimeSTT library
- **Multiple listening modes**:
  - Wake word mode: Say "hey windows use" to activate
  - Push-to-talk mode: Press Enter to start/stop speaking
  - Continuous mode: Always listening for commands
- **Advanced voice activity detection** using Silero VAD
- **Low-latency processing** for responsive interaction

### Text-to-Speech (TTS)
- **Natural voice output** using pyttsx3
- **Multiple voice options** (male/female/default)
- **Adjustable speech rate** (words per minute)
- **Volume control** and voice customization

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install voice dependencies
pip install RealtimeSTT pyaudio pyttsx3

# Or install all dependencies
pip install -e .
```

### 2. Run with Voice Support

```bash
python main.py
```

### 3. Enable Voice Mode

Type `voice` in the main interface to access voice functionality:

```
💬 You: voice
```

Choose from:
1. **Wake word mode** - Say "hey windows use" to activate
2. **Push-to-talk mode** - Press Enter to start/stop speaking  
3. **Continuous mode** - Always listening for commands
4. **Test voice output** - Test TTS functionality
5. **Back to text mode** - Return to text input

## 🛠️ Voice Modes Explained

### Wake Word Mode
- **Activation**: Say "hey windows use" followed by your command
- **Example**: "hey windows use, open notepad and type hello world"
- **Best for**: Hands-free operation, avoiding accidental activation
- **Timeout**: 5 minutes of inactivity returns to wake word listening

### Push-to-Talk Mode
- **Activation**: Press Enter to start speaking, Enter again to stop
- **Example**: Press Enter → "open calculator" → Press Enter
- **Best for**: Controlled interaction, avoiding background noise
- **Timeout**: 30 seconds maximum per command

### Continuous Mode
- **Activation**: Always listening for commands
- **Example**: Just start speaking "open chrome browser"
- **Best for**: Quick commands, always-on assistant
- **Timeout**: 5 minutes of inactivity stops listening

## 🎯 Voice Commands Examples

### Basic Commands
- "Open notepad"
- "Click on the start button"
- "Type hello world"
- "Scroll down"
- "Take a screenshot"

### Complex Commands
- "Open Chrome browser and search for Python tutorials"
- "Open notepad, type my shopping list, and save it"
- "Click on the calculator app and calculate 25 times 4"
- "Open file explorer and navigate to documents folder"

### Voice Feedback
The agent can respond with voice output for:
- Task completion confirmations
- Error messages and troubleshooting
- Step-by-step guidance
- Status updates

## 🔧 Configuration

### Voice Service Settings

```python
from windows_use.agent.voice.service import VoiceService

# Create voice service with custom settings
voice_service = VoiceService(
    wake_word="hey windows use",  # Custom wake word
    language="en",                # Language code
    model="whisper",             # STT model (whisper/deepspeech)
    voice_mode="wake_word"       # Listening mode
)
```

### TTS Settings

```python
# Customize TTS
voice_service.speak(
    text="Hello world!",
    voice="female",    # default, male, female
    rate=200          # words per minute
)
```

## 🛠️ Voice Tools for Agent

The agent has access to these voice tools:

### Voice Input Tool
```python
# Listen for voice input
voice_input_tool(
    duration=10,                    # seconds to listen
    wake_word="hey windows use",    # wake word
    mode="wake_word"               # listening mode
)
```

### Voice Output Tool
```python
# Convert text to speech
voice_output_tool(
    text="Task completed successfully!",
    voice="default",               # voice type
    rate=200                      # speech rate
)
```

### Voice Mode Tool
```python
# Control voice functionality
voice_mode_tool(mode="on")        # enable voice
voice_mode_tool(mode="off")       # disable voice
voice_mode_tool(mode="toggle")    # toggle voice
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "Voice service not available"
- **Check**: Audio devices are connected and working
- **Check**: Microphone permissions are granted
- **Check**: Dependencies are installed: `pip install RealtimeSTT pyaudio pyttsx3`

#### 2. "Import error" for RealtimeSTT
- **Solution**: Install RealtimeSTT: `pip install RealtimeSTT`
- **Note**: May require additional audio libraries on some systems

#### 3. "TTS engine not available"
- **Check**: Audio output devices are working
- **Check**: pyttsx3 is installed: `pip install pyttsx3`
- **Check**: System audio drivers are up to date

#### 4. Poor voice recognition accuracy
- **Solution**: Speak clearly and at normal volume
- **Solution**: Reduce background noise
- **Solution**: Use push-to-talk mode for better control
- **Solution**: Adjust sensitivity settings in VoiceService

#### 5. Wake word not detected
- **Solution**: Speak the wake word clearly: "hey windows use"
- **Solution**: Check microphone is working
- **Solution**: Try push-to-talk mode as alternative

### Testing Voice Functionality

Run the test script to verify voice setup:

```bash
python test_voice.py
```

This will test:
- TTS engine initialization
- Voice service availability
- Voice tools functionality

## 📁 File Structure

```
windows_use/
├── agent/
│   ├── voice/
│   │   ├── __init__.py
│   │   └── service.py          # VoiceService class
│   ├── tools/
│   │   ├── service.py          # Voice tools (voice_input_tool, etc.)
│   │   └── views.py            # Voice tool schemas
│   └── service.py              # Updated agent with voice tools
├── main.py                     # Updated with voice interface
└── test_voice.py              # Voice functionality test script
```

## 🔮 Future Enhancements

### Planned Features
- **Custom wake words**: Train your own wake word models
- **Voice profiles**: Save user voice preferences
- **Multi-language support**: Support for multiple languages
- **Voice commands**: Shortcut commands for common tasks
- **Audio feedback**: Sound effects for different actions
- **Voice training**: Improve recognition for specific users

### Advanced Integration
- **Cloud TTS**: Integration with ElevenLabs, OpenAI TTS
- **Cloud STT**: Integration with cloud-based speech recognition
- **Voice cloning**: Custom voice generation
- **Emotion detection**: Detect user emotion from voice
- **Speaker identification**: Recognize different users

## 📚 Dependencies

### Required
- `RealtimeSTT>=0.3.104` - Real-time speech-to-text
- `pyaudio>=0.2.11` - Audio I/O
- `pyttsx3>=2.90` - Text-to-speech

### Optional (for advanced features)
- `openai-whisper` - Alternative STT models
- `elevenlabs` - High-quality TTS
- `azure-cognitiveservices-speech` - Azure Speech Services

## 🤝 Contributing

To contribute to voice functionality:

1. **Report issues**: Use GitHub issues for bugs and feature requests
2. **Test thoroughly**: Test on different audio setups and environments
3. **Document changes**: Update this README for any new features
4. **Follow patterns**: Use existing code patterns for consistency

## 📄 License

Voice functionality follows the same MIT license as the main Windows-Use project.

---

**Happy voice automation! 🎤🤖**

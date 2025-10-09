# 🚀 Setup Guide for Users

Welcome to Windows-Use AI! This guide will help you get started.

## 📥 Installation

1. **Download** the installer: `Windows-Use AI Setup 1.0.0.exe`
2. **Run** the installer and follow the setup wizard
3. **Accept** the terms and conditions
4. **Launch** the application from your desktop or start menu

## ⚙️ First-Time Configuration

### Step 1: Get Your Google AI API Key

The application requires a Google AI API key to function:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Get API Key"**
4. Copy your API key

### Step 2: Configure the Application

#### Option A: Using Settings Dialog (Coming Soon)

The app will prompt you for your API key on first launch.

#### Option B: Manual Configuration

1. Navigate to the installation directory:
   ```
   C:\Program Files\Windows-Use AI\
   ```

2. Create a file named `.env` (note the dot at the beginning)

3. Add your API key:
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   ENABLE_TTS=true
   ```

4. Save the file and restart the application

### Step 3: Start Using the App

1. Type your command in the input box
2. Click **Submit** or press **Enter**
3. Watch the AI agent perform the task!

## 🎤 Optional: Enable Voice Control

For voice control features, you'll need a Deepgram API key:

1. Sign up at [Deepgram](https://deepgram.com/)
2. Get your API key from the console
3. Add to your `.env` file:
   ```env
   DEEPGRAM_API_KEY=your_deepgram_key_here
   ```
4. Restart the application

## 🔊 Optional: Enable Text-to-Speech

For the agent to speak responses:

1. Sign up at [ElevenLabs](https://elevenlabs.io/) (free tier available)
2. Get your API key
3. Add to your `.env` file:
   ```env
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   ENABLE_TTS=true
   ```
4. Restart the application

## 📝 Example Commands

Try these commands to get started:

- "Open Notepad"
- "Search for Python on Google"
- "Take a screenshot"
- "Open File Explorer and navigate to Documents"
- "Create a new folder on the desktop called 'Test'"
- "Close all Chrome windows"

## 🛡️ Safety Tips

1. **Start Simple**: Begin with basic commands to understand how the agent works
2. **Monitor Actions**: Watch what the agent does, especially at first
3. **Backup Important Data**: Keep backups before using automation features
4. **Review Tasks**: Understand what you're asking before submitting
5. **Use Sandbox**: Test in a safe environment when possible

## ⚠️ Important Notes

### What the Agent Can Do

- ✅ Open and close applications
- ✅ Click buttons and UI elements
- ✅ Type text and fill forms
- ✅ Navigate windows and menus
- ✅ Take screenshots
- ✅ Run PowerShell commands
- ✅ Search and browse the web

### What to Be Careful With

- ⚠️ System settings changes
- ⚠️ File deletions
- ⚠️ Administrative tasks
- ⚠️ Sensitive data entry
- ⚠️ Financial transactions

## 🐛 Troubleshooting

### Application Won't Start

1. Check that your `.env` file exists and contains your API key
2. Verify the API key is correct
3. Check Windows Event Viewer for errors
4. Try running as Administrator

### Agent Doesn't Respond

1. Check your internet connection
2. Verify your API key is valid and has quota
3. Check the console logs (press F12 in the app)
4. Restart the application

### API Key Errors

```
Error: GOOGLE_API_KEY not set
```

**Solution**: Create the `.env` file with your API key as described above.

### Performance Issues

1. Close other resource-intensive applications
2. Increase `MAX_STEPS` in `.env` if tasks are too complex
3. Disable TTS if not needed: `ENABLE_TTS=false`

## 💡 Tips for Best Results

1. **Be Specific**: Clear, detailed commands work best
   - ❌ "Open something"
   - ✅ "Open Google Chrome and go to youtube.com"

2. **One Task at a Time**: Break complex tasks into steps
   - ❌ "Open Chrome, search for Python, download it, and install it"
   - ✅ "Open Chrome and search for Python download"

3. **Provide Context**: Tell the agent what you want to achieve
   - ❌ "Click the button"
   - ✅ "Click the Submit button in the contact form"

4. **Use Memory**: The agent remembers your conversation
   - "Open Notepad" → "Type 'Hello World'" → "Save it to Desktop"

## 🆘 Getting Help

Need assistance?

- **Documentation**: Check the full guide at [GitHub](https://github.com/CursorTouch/Windows-Use)
- **Discord**: Join our community at [Discord](https://discord.com/invite/Aue9Yj2VzS)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/CursorTouch/Windows-Use/issues)
- **Twitter**: Follow [@CursorTouch](https://x.com/CursorTouch) for updates

## 🔄 Updates

The application will check for updates automatically. When an update is available, you'll be prompted to download and install it.

To manually check for updates:
1. Open the application
2. Go to **Help** → **Check for Updates**

## 📄 License

This software is licensed under the MIT License. See LICENSE.txt in the installation directory.

## ⭐ Enjoying the App?

If you find Windows-Use AI helpful:
- ⭐ Star us on [GitHub](https://github.com/CursorTouch/Windows-Use)
- 🐦 Share on [Twitter](https://twitter.com/intent/tweet?text=Check%20out%20Windows-Use%20AI!)
- 💬 Join our [Discord](https://discord.com/invite/Aue9Yj2VzS) community

---

**Happy Automating!** 🚀


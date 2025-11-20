<div align="center">

# Yuki AI

<img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
<img src="https://img.shields.io/badge/platform-Windows%207-11-blue" alt="Platform: Windows 7 to 11">
<a href="https://github.com/CursorTouch/windows-use/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</a>

**Your AI companion that understands and controls Windows**

</div>

---

## What is Yuki AI?

Yuki AI is an intelligent automation agent that sees, thinks, and acts on your Windows computer. Unlike traditional automation tools, Yuki can:

- **See your screen** using AI vision to understand what's displayed
- **Understand context** by reading UI elements, text, and visual content
- **Take action** by clicking, typing, opening apps, and executing commands
- **Converse naturally** in plain English to get things done

Whether you need to automate repetitive tasks, interact with web applications, or control desktop software, Yuki AI bridges the gap between natural language and Windows automation.

---

## Key Features

### Intelligent Screen Detection
- **UI Automation**: Detects buttons, inputs, and controls in native Windows apps
- **Vision Mode**: Uses AI to see and understand web content and complex interfaces
- **Precise Coordination**: Accurately clicks and interacts with screen elements

### Comprehensive Tool Set
- **Launch Tool**: Open any application from the Start Menu
- **Click Tool**: Interact with buttons, links, and UI elements
- **Type Tool**: Input text into fields with smart clearing and formatting
- **Shell Tool**: Execute PowerShell commands directly
- **Scroll Tool**: Navigate through long content and lists
- **And more**: Drag, move, keyboard shortcuts, clipboard operations

### Smart Task Planning
- Breaks down complex tasks into actionable steps
- Adapts when things go wrong and finds alternative solutions
- Provides real-time status updates during execution
- Learns from conversation history for context-aware responses

### Activity Tracking
- Monitors your computer usage and productivity
- Provides insights about focus time and app usage
- Captures screenshots with AI-powered activity analysis
- Query your activity history with natural language

### Modern Web Interface
- ChatGPT-like conversational UI
- Real-time task execution status
- Settings management and API key configuration
- Scheduled tasks and background automation

---

## Quick Start

### Prerequisites

- **Python 3.12 or higher**
- **Windows 7, 8, 10, or 11**
- **Google API Key** (for Gemini AI)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CursorTouch/Windows-Use.git
   cd Windows-Use
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key:**
   
   Create a `config/api_keys.json` file:
   ```json
   {
     "google_api_key": "YOUR_GOOGLE_API_KEY",
     "enable_vision": true,
     "browser": "chrome",
     "max_steps": 50
   }
   ```

4. **Start Yuki AI:**

   Choose your preferred interface:

   **Web Interface (Recommended):**
   ```bash
   start_api_server.bat    # Terminal 1
   start_frontend.bat      # Terminal 2
   ```
   Then open http://localhost:3000

   **Command Line:**
   ```bash
   python main.py
   ```

   **Desktop GUI:**
   ```bash
   python gui_app.py
   ```

---

## Usage Examples

### Basic Python Script

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
import os

# Initialize AI model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Create Yuki AI agent
agent = Agent(
    llm=llm,
    browser="chrome",
    use_vision=True,  # Enable vision for web automation
    max_steps=50
)

# Execute a task
result = agent.invoke("Open Calculator and compute 15 * 24")
print(result.content)
```

### Example Tasks

**Desktop Automation:**
```
"Open Notepad and write a haiku about AI"
"Search for 'productivity' in File Explorer"
"Change Windows theme to dark mode"
```

**Web Automation:**
```
"Go to GitHub and search for Python automation projects"
"Open Gmail and check my unread emails"
"Navigate to Amazon and search for wireless keyboards"
```

**System Operations:**
```
"Show me system information and CPU usage"
"List all running programs"
"Create a scheduled task to open Spotify at 9 AM"
```

**Activity Tracking:**
```
"How focused was I today?"
"What apps did I use most this week?"
"What was I doing at 3 PM yesterday?"
```

---

## Configuration

### Settings Overview

Configure Yuki AI through the web interface or `config/api_keys.json`:

| Setting | Description | Default |
|---------|-------------|---------|
| `enable_vision` | Use AI vision for screen analysis | `false` |
| `browser` | Default browser (chrome/edge/firefox) | `chrome` |
| `max_steps` | Maximum steps per task | `50` |
| `consecutive_failures` | Retry limit before giving up | `3` |
| `cache_timeout` | Screen state cache duration (seconds) | `2.0` |
| `literal_mode` | Strict command interpretation | `true` |
| `enable_tts` | Text-to-speech responses | `false` |
| `enable_activity_tracking` | Track computer usage | `true` |

### Vision Mode

**When to enable Vision Mode:**
- Web automation (websites don't expose UI elements)
- Games and custom UIs
- Complex visual interfaces
- When UI Automation fails to detect elements

**Trade-offs:**
- Captures and analyzes screenshots (slower but more capable)
- Higher API costs (vision model usage)
- Better accuracy for web content

---

## Architecture

### Core Components

```
Yuki AI
|-- Agent (windows_use/agent/)
|   |-- Service: Task planning and execution
|   |-- Tools: Click, type, launch, shell, etc.
|   |-- Prompt: System instructions and templates
|   |-- Memory: Conversation and context management
|
|-- Desktop (windows_use/desktop/)
|   |-- Service: Window management and state
|   |-- UI Automation integration
|
|-- Tree (windows_use/tree/)
|   |-- Service: Element detection and traversal
|   |-- Precise Detection: App-specific element finding
|   |-- Views: Node representations
|
|-- Tracking (windows_use/tracking/)
|   |-- Activity Tracker: Usage monitoring
|   |-- Screenshot Service: Periodic captures
|   |-- Analyzer: AI-powered activity analysis
|
|-- API Server (api_server.py)
    |-- RESTful endpoints
    |-- Streaming responses
    |-- Settings management
```

### How It Works

1. **Input**: User provides natural language task
2. **Planning**: Agent breaks task into steps using LLM reasoning
3. **Perception**: Desktop service captures screen state via:
   - UI Automation (native apps)
   - Vision mode (screenshots + AI analysis)
4. **Action**: Agent selects and executes appropriate tools
5. **Observation**: Checks result and decides next action
6. **Iteration**: Repeats until task is complete or max steps reached

---

## Advanced Usage

### Custom Tools

Extend Yuki AI with custom tools:

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(description="Parameter description")

@tool("My Custom Tool", args_schema=MyToolInput)
def my_custom_tool(param: str) -> str:
    """Tool description for the AI"""
    # Your implementation
    return f"Result: {param}"

# Add to agent
agent = Agent(
    llm=llm,
    additional_tools=[my_custom_tool]
)
```

### Programmatic Control

```python
# Stop current task
agent.stop()

# Clear conversation history
agent.conversation_history.clear()

# Get desktop state
desktop_state = agent.desktop.get_state(use_vision=True)
print(f"Active app: {desktop_state.active_app.name}")
print(f"Interactive elements: {len(desktop_state.tree_state.interactive_nodes)}")
```

### Scheduled Tasks

Schedule recurring automation via the web interface or API:

```python
import requests

response = requests.post("http://127.0.0.1:8000/api/scheduled-tasks", json={
    "name": "spotify",
    "run_at": "09:00",
    "repeat_interval_seconds": 86400  # Daily
})
```

---

## Troubleshooting

### Screen Detection Issues

**Problem**: Agent can't see elements on screen

**Solutions:**
1. Enable **Vision Mode** for web content
2. Check if the app uses standard Windows controls
3. Ensure the window is focused and visible
4. Try running as Administrator

### Performance Issues

**Problem**: Agent is slow or hanging

**Solutions:**
1. Reduce `cache_timeout` for faster updates
2. Limit `max_steps` for quicker termination
3. Close unnecessary background apps
4. Check your internet connection (API calls)

### Tool Failures

**Problem**: Clicks/types in wrong location

**Solutions:**
1. Ensure desktop state is refreshed after window switches
2. Verify screen DPI scaling settings
3. Check if the target window is maximized
4. Enable Vision Mode for better accuracy

---

## API Reference

### Agent Class

```python
Agent(
    llm: BaseChatModel,                    # Language model instance
    browser: str = "chrome",               # Default browser
    use_vision: bool = False,              # Enable vision mode
    max_steps: int = 50,                   # Maximum task steps
    consecutive_failures: int = 3,         # Failure threshold
    enable_conversation: bool = True,      # Context awareness
    literal_mode: bool = True,             # Strict interpretation
    enable_tts: bool = False,              # Text-to-speech
    enable_activity_tracking: bool = True  # Usage tracking
)
```

### Agent Methods

- `invoke(query: str) -> AgentResult`: Execute a task
- `stop()`: Stop current execution
- `show_status(category, action, message)`: Display status

### Desktop Methods

- `get_state(use_vision: bool, target_app: str) -> DesktopState`
- `get_apps() -> list[App]`
- `launch_app(name: str) -> tuple[str, str, int]`
- `switch_app(name: str) -> tuple[str, int]`
- `get_screenshot(scale: float) -> Image`

---

## Contributing

Contributions are welcome! Areas for improvement:

- Test coverage and automated testing
- Support for additional browsers
- UI/UX enhancements
- Documentation and examples
- New tool implementations
- Bug fixes and performance optimizations

---

## Safety & Limitations

### Caution

Yuki AI interacts directly with your Windows OS at the GUI layer. While designed to act intelligently and safely, it can:

- Make mistakes that cause unintended actions
- Modify system settings or files
- Execute commands with your user permissions
- Interact with sensitive applications

**Recommendations:**
- Test in a sandbox or virtual machine first
- Monitor execution for critical tasks
- Review scheduled tasks periodically
- Don't share API keys or sensitive data

### Limitations

- **Web Content**: Requires Vision Mode for reliable web automation
- **Performance**: Vision mode is slower and more expensive
- **Accuracy**: May misinterpret complex UIs or ambiguous instructions
- **Windows Only**: Currently supports Windows 7-11 only
- **English**: Best performance with English language interfaces

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Acknowledgments

Built with:
- [LangChain](https://github.com/langchain-ai/langchain) - AI orchestration
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI models
- [uiautomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows) - Windows UI automation
- [PyAutoGUI](https://github.com/asweigart/pyautogui) - GUI automation
- [Next.js](https://nextjs.org/) - Frontend framework

---

<div align="center">

**Built with love for Windows automation**

[Report Bug](https://github.com/CursorTouch/Windows-Use/issues) - [Request Feature](https://github.com/CursorTouch/Windows-Use/issues)

</div>

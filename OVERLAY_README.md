# Agent Status Overlay

A transparent overlay UI that shows real-time agent execution status without interfering with your workflow.

## Features

- **Always on top**: Stays visible above all other windows
- **Transparent**: 85% opacity so it doesn't block your view
- **Draggable**: Click and drag the title to move it around
- **Real-time updates**: Shows agent iteration, plans, thoughts, and tool execution
- **Non-intrusive**: Doesn't interfere with window switching or focus

## What It Shows

The overlay displays:

- **Phase**: Current execution phase (Starting, Executing, Completed, etc.)
- **Step**: Current iteration number and max steps
- **Action**: Current tool being executed (Click Tool, Type Tool, etc.)
- **Details**: Additional details about the current action
- **Evaluate**: Agent's evaluation of the current state
- **Memory**: Agent's memory retrieval information
- **Plan**: Agent's plan for the next steps
- **Thought**: Agent's reasoning process
- **Result**: Tool execution results
- **Time**: Timestamp of last update
- **Progress Bar**: Visual progress indicator

## Usage

The overlay starts automatically when you run the main application:

```bash
python main.py
```

You'll see a message:
```
Starting overlay UI...
Overlay UI started successfully!
```

## Controls

- **Move**: Click and drag the title bar to move the overlay
- **Minimize**: Click the "−" button to minimize/restore the window
- **Close**: Click the "×" button to close the overlay

## Testing

To test the overlay independently:

```bash
python test_overlay.py
```

This will show simulated agent execution with various status updates.

## Troubleshooting

### Overlay doesn't appear
- Make sure tkinter is installed: `pip install tk`
- Check if another overlay instance is already running
- Try running the test script first: `python test_overlay.py`

### Overlay blocks other windows
- The overlay is designed to stay on top but not block interaction
- If it's in the way, drag it to a corner using the title bar
- Use the minimize button to hide it temporarily

### Performance issues
- The overlay updates every 100ms for smooth real-time display
- If you experience lag, you can close the overlay and the agent will still work normally

## Technical Details

- Built with tkinter for cross-platform compatibility
- Uses threading to avoid blocking the main agent execution
- Thread-safe status updates via queue system
- Automatically integrates with agent logging system
- Graceful fallback if overlay fails to start

## Files

- `overlay_ui.py`: Main overlay UI implementation
- `overlay_logger.py`: Logging integration (optional)
- `test_overlay.py`: Test script for overlay functionality
- Modified `windows_use/agent/service.py`: Agent integration
- Modified `main.py`: Application startup integration

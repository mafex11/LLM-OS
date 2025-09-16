from windows_use.agent.tools.views import Click, Type, Launch, Scroll, Drag, Move, Shortcut, Key, Wait, Scrape,Done, Clipboard, Shell, Switch, Resize, Human, VoiceInput, VoiceOutput, VoiceMode
from windows_use.desktop.service import Desktop
from humancursor import SystemCursor
from markdownify import markdownify
from langchain.tools import tool
from typing import Literal
import uiautomation as uia
import pyperclip as pc
import pyautogui as pg
import requests

cursor=SystemCursor()
pg.FAILSAFE=False
pg.PAUSE=1.0

@tool('Done Tool',args_schema=Done)
def done_tool(answer:str,desktop:Desktop=None):
    '''To indicate that the task is completed'''
    return answer

@tool('Launch Tool',args_schema=Launch)
def launch_tool(name: str,desktop:Desktop=None) -> str:
    'Launch an application present in start menu (e.g., "notepad", "calculator", "chrome"). If already running, switches to existing window.'
    app_name,response,status=desktop.launch_app(name)
    if status!=0:
        return f'Failed to launch {name.title()}. {response}'
    else:
        # Check if this was a switch to existing app or a new launch
        if "already running" in response.lower():
            # App was already running and we switched to it
            pg.sleep(1.0)  # Brief wait for switch to complete
            desktop.get_state(use_vision=False)
            return f'{name.title()} was already running. Switched to existing window. Desktop state refreshed. IMPORTANT: Use fresh coordinates from the updated desktop state for all subsequent actions.'
        else:
            # New app was launched, wait for it to load
            consecutive_waits=3
            for _ in range(consecutive_waits):
                if not desktop.is_app_running(name):
                    pg.sleep(1.25)
                else:
                    # Wait a bit more for the app to fully load and render
                    pg.sleep(2.0)
                    # Refresh desktop state to get updated coordinates
                    desktop.get_state(use_vision=False)
                    return f'{name.title()} launched and desktop state refreshed. IMPORTANT: Use fresh coordinates from the updated desktop state for all subsequent actions.'
            return f'Launching {name.title()} wait for it to come load.'

@tool('Shell Tool',args_schema=Shell)
def shell_tool(command: str,desktop:Desktop=None) -> str:
    'Execute PowerShell commands and return the output with status code'
    response,status=desktop.execute_command(command)
    return f'Status Code: {status}\nResponse: {response}'

@tool('Clipboard Tool',args_schema=Clipboard)
def clipboard_tool(mode: Literal['copy', 'paste'], text: str = None,desktop:Desktop=None)->str:
    'Copy text to clipboard or retrieve current clipboard content. Use "copy" mode with text parameter to copy, "paste" mode to retrieve.'
    if mode == 'copy':
        if text:
            pc.copy(text)  # Copy text to system clipboard
            return f'Copied "{text}" to clipboard'
        else:
            raise ValueError("No text provided to copy")
    elif mode == 'paste':
        clipboard_content = pc.paste()  # Get text from system clipboard
        return f'Clipboard Content: "{clipboard_content}"'
    else:
        raise ValueError('Invalid mode. Use "copy" or "paste".')
    
@tool('Switch Tool',args_schema=Switch)
def switch_tool(name: str,desktop:Desktop=None) -> str:
    'Switch to a specific application window (e.g., "notepad", "calculator", "chrome", etc.) and bring to foreground.'
    _,status=desktop.switch_app(name)
    if status!=0:
        return f'Failed to switch to {name.title()} window.'
    else:
        return f'Switched to {name.title()} window.'
    
@tool("Resize Tool",args_schema=Resize)
def resize_tool(name: str,loc:tuple[int,int]=None,size:tuple[int,int]=None,desktop:Desktop=None) -> str:
    'Resize a specific application window (e.g., "notepad", "calculator", "chrome", etc.) to a specific size and location.'
    response,_=desktop.resize_app(name,loc,size)
    return response

@tool('Click Tool',args_schema=Click)
def click_tool(loc:tuple[int,int],button:Literal['left','right','middle']='left',clicks:int=1,desktop:Desktop=None)->str:
    'Click on UI elements at specific coordinates. Supports left/right/middle mouse buttons and single/double/triple clicks.'
    x,y=loc
    
    # Validate coordinates are within screen bounds
    screen_width, screen_height = pg.size()
    if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
        return f'Error: Coordinates ({x},{y}) are outside screen bounds ({screen_width}x{screen_height})'
    
    # Move cursor to the target location
    cursor.move_to(loc)
    pg.sleep(0.1)  # Small delay to ensure cursor movement completes
    
    # Get the element under cursor and validate it's clickable
    control=desktop.get_element_under_cursor()
    parent=control.GetParentControl()
    
    # For search bars and input fields, try to ensure we're clicking on the right element
    if control.ControlTypeName in ['EditControl', 'ComboBoxControl']:
        # Double-check we're on the right element by verifying coordinates are within bounds
        box = control.BoundingRectangle
        if not (box.left <= x <= box.right and box.top <= y <= box.bottom):
            # If coordinates are outside the element bounds, try clicking the center
            center_x, center_y = box.xcenter(), box.ycenter()
            cursor.move_to((center_x, center_y))
            pg.sleep(0.1)
            control = desktop.get_element_under_cursor()
            x, y = center_x, center_y
    
    # Perform the click
    if parent.Name=="Desktop":
        pg.click(x=x,y=y,button=button,clicks=clicks)
    else:
        pg.mouseDown()
        pg.click(button=button,clicks=clicks)
        pg.mouseUp()
    
    pg.sleep(1.0)
    num_clicks={1:'Single',2:'Double',3:'Triple'}
    return f'{num_clicks.get(clicks)} {button} Clicked on {control.Name} Element with ControlType {control.ControlTypeName} at ({x},{y}).'

@tool('Type Tool',args_schema=Type)
def type_tool(loc:tuple[int,int],text:str,clear:Literal['true','false']='false',caret_position:Literal['start','idle','end']='idle',press_enter:Literal['true','false']='false',desktop:Desktop=None):
    'Type text into input fields, text areas, or focused elements. Set clear=True to replace existing text, False to append. Click on target element coordinates first and start typing.'
    x,y=loc
    cursor.click_on(loc)
    control=desktop.get_element_under_cursor()
    if caret_position == 'start':
        pg.press('home')
    elif caret_position == 'end':
        pg.press('end')
    else:
        pass
    if clear=='true':
        pg.hotkey('ctrl','a')
        pg.press('backspace')
    pg.typewrite(text,interval=0.1)
    if press_enter=='true':
        pg.press('enter')
    return f'Typed {text} on {control.Name} Element with ControlType {control.ControlTypeName} at ({x},{y}).'

@tool('Scroll Tool',args_schema=Scroll)
def scroll_tool(loc:tuple[int,int]=None,type:Literal['horizontal','vertical']='vertical',direction:Literal['up','down','left','right']='down',wheel_times:int=1,desktop:Desktop=None)->str:
    'Move cursor to a specific location or current location, start scrolling in the specified direction. Use wheel_times to control scroll amount (1 wheel = ~3-5 lines). Essential for navigating lists, web pages, and long content.'
    if loc:
        cursor.move_to(loc)
    match type:
        case 'vertical':
            match direction:
                case 'up':
                    uia.WheelUp(wheel_times)
                case 'down':
                    uia.WheelDown(wheel_times)
                case _:
                    return 'Invalid direction. Use "up" or "down".'
        case 'horizontal':
            match direction:
                case 'left':
                    pg.keyDown('Shift')
                    pg.sleep(0.05)
                    uia.WheelUp(wheel_times)
                    pg.sleep(0.05)
                    pg.keyUp('Shift')
                case 'right':
                    pg.keyDown('Shift')
                    pg.sleep(0.05)
                    uia.WheelDown(wheel_times)
                    pg.sleep(0.05)
                    pg.keyUp('Shift')
                case _:
                    return 'Invalid direction. Use "left" or "right".'
        case _:
            return 'Invalid type. Use "horizontal" or "vertical".'
    return f'Scrolled {type} {direction} by {wheel_times} wheel times.'

@tool('Drag Tool',args_schema=Drag)
def drag_tool(from_loc:tuple[int,int],to_loc:tuple[int,int],desktop:Desktop=None)->str:
    'Drag and drop operation from source coordinates to destination coordinates. Useful for moving files, resizing windows, or drag-and-drop interactions.'
    control=desktop.get_element_under_cursor()
    x1,y1=from_loc
    x2,y2=to_loc
    cursor.drag_and_drop(from_loc,to_loc)
    return f'Dragged the {control.Name} element with ControlType {control.ControlTypeName} from ({x1},{y1}) to ({x2},{y2}).'

@tool('Move Tool',args_schema=Move)
def move_tool(to_loc:tuple[int,int],desktop:Desktop=None)->str:
    'Move mouse cursor to specific coordinates without clicking. Useful for hovering over elements or positioning cursor before other actions.'
    x,y=to_loc
    cursor.move_to(to_loc)
    return f'Moved the mouse pointer to ({x},{y}).'

@tool('Shortcut Tool',args_schema=Shortcut)
def shortcut_tool(shortcut:list[str],desktop:Desktop=None):
    'Execute keyboard shortcuts using key combinations. Pass keys as list (e.g., ["ctrl", "c"] for copy, ["alt", "tab"] for app switching, ["win", "r"] for Run dialog).'
    pg.hotkey(*shortcut)
    return f'Pressed {'+'.join(shortcut)}.'

@tool('Key Tool',args_schema=Key)
def key_tool(key:str='',desktop:Desktop=None)->str:
    'Press individual keyboard keys. Supports special keys like "enter", "escape", "tab", "space", "backspace", "delete", arrow keys ("up", "down", "left", "right"), function keys ("f1"-"f12").'
    pg.press(key)
    return f'Pressed the key {key}.'

@tool('Wait Tool',args_schema=Wait)
def wait_tool(duration:int,desktop:Desktop=None)->str:
    'Pause execution for specified duration in seconds. Useful for waiting for applications to load, animations to complete, or adding delays between actions.'
    pg.sleep(duration)
    return f'Waited for {duration} seconds.'

@tool('Scrape Tool',args_schema=Scrape)
def scrape_tool(url:str,desktop:Desktop=None)->str:
    'Fetch and convert webpage content to markdown format. Provide full URL including protocol (http/https). Returns structured text content suitable for analysis.'
    response=requests.get(url,timeout=10)
    html=response.text
    content=markdownify(html=html)
    return f'Scraped the contents of the entire webpage:\n{content}'

@tool('Human Tool',args_schema=Human)
def human_tool(question:str,desktop:Desktop=None)->str:
    'Ask the user a question for clarification, permission, or additional information. Use this when you need user input before proceeding with an action.'
    return f"❓ USER QUESTION: {question}\n\nPlease respond with your answer, and I'll continue based on your response."

@tool('Voice Input Tool',args_schema=VoiceInput)
def voice_input_tool(duration:int,wake_word:str,mode:Literal['push_to_talk','continuous','wake_word'],desktop:Desktop=None)->str:
    'Listen for voice input for specified duration and convert to text. Supports wake word activation and different listening modes.'
    try:
        from windows_use.agent.voice.service import VoiceService
        
        # Create voice service instance
        voice_service = VoiceService(wake_word=wake_word, voice_mode=mode, model="base")
        
        if not voice_service.is_available():
            return "Voice service not available. Please check audio devices and dependencies."
        
        # Start listening
        transcription_result = None
        
        def on_transcription(text: str):
            nonlocal transcription_result
            transcription_result = text
        
        def on_wake_word():
            print(f"🎯 Wake word '{wake_word}' detected! Listening for command...")
        
        success = voice_service.start_listening(
            duration=duration,
            on_transcription=on_transcription,
            on_wake_word=on_wake_word if mode == 'wake_word' else None
        )
        
        if not success:
            return "Failed to start voice listening. Please check microphone permissions."
        
        # Wait for transcription or timeout
        import time
        start_time = time.time()
        while time.time() - start_time < duration and transcription_result is None:
            time.sleep(0.1)
        
        voice_service.stop_listening()
        
        if transcription_result:
            return f"Voice input received: '{transcription_result}'"
        else:
            return f"No voice input detected within {duration} seconds."
            
    except ImportError:
        return "Voice functionality not available. Please install RealtimeSTT and audio dependencies."
    except Exception as e:
        return f"Voice input error: {str(e)}"

@tool('Voice Output Tool',args_schema=VoiceOutput)
def voice_output_tool(text:str,voice:Literal['default','male','female']='default',rate:int=200,desktop:Desktop=None)->str:
    'Convert text to speech and play audio output. Useful for providing voice feedback to users.'
    try:
        from windows_use.agent.voice.service import VoiceService
        
        # Create voice service instance
        voice_service = VoiceService()
        
        if not voice_service.is_available():
            return "Voice output not available. Please check audio devices and TTS engine."
        
        # Speak the text
        success = voice_service.speak(text, voice=voice, rate=rate)
        
        if success:
            return f"Spoke: '{text}' (Voice: {voice}, Rate: {rate} WPM)"
        else:
            return f"Failed to speak: '{text}'"
            
    except ImportError:
        return "Voice functionality not available. Please install TTS dependencies."
    except Exception as e:
        return f"Voice output error: {str(e)}"

@tool('Voice Mode Tool',args_schema=VoiceMode)
def voice_mode_tool(mode:Literal['on','off','toggle'],desktop:Desktop=None)->str:
    'Enable, disable, or toggle voice interaction mode. Controls whether voice input/output is active.'
    try:
        from windows_use.agent.voice.service import VoiceService
        
        # Create voice service instance
        voice_service = VoiceService()
        
        if mode == 'on':
            voice_service.is_voice_enabled = True
            return "Voice mode enabled. Voice input and output are now active."
        elif mode == 'off':
            voice_service.is_voice_enabled = False
            return "Voice mode disabled. Voice input and output are now inactive."
        else:  # toggle
            new_state = voice_service.toggle_voice()
            status = "enabled" if new_state else "disabled"
            return f"Voice mode toggled. Voice functionality is now {status}."
            
    except ImportError:
        return "Voice functionality not available. Please install voice dependencies."
    except Exception as e:
        return f"Voice mode error: {str(e)}"
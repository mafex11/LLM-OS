from windows_use.agent.tools.views import Click, Type, Launch, Scroll, Drag, Move, Shortcut, Key, Wait, Scrape,Done, Clipboard, Shell, Switch, Resize, Human, System
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
pg.PAUSE=0.01  # Reduced from 0.1 for better performance

def get_optimal_click_delay(control_type: str) -> float:
    """
    Return optimal post-click delay based on control type.
    
    Most modern Windows apps respond instantly (<100ms).
    Only legacy/complex controls need longer delays.
    """
    # No delay needed for most controls
    instant_controls = {
        'ButtonControl', 'CheckBoxControl', 'RadioButtonControl',
        'TabItemControl', 'ListItemControl', 'MenuItemControl'
    }
    
    # Minimal delay for input controls (keyboard focus)
    fast_controls = {
        'EditControl', 'ComboBoxControl', 'HyperlinkControl'
    }
    
    # Longer delay for heavy operations
    slow_controls = {
        'MenuControl',  # Menu needs to render
        'ApplicationControl'  # App launch/switch
    }
    
    if control_type in instant_controls:
        return 0.05  # 50ms - just for stability
    elif control_type in fast_controls:
        return 0.15  # 150ms - allow focus to settle
    elif control_type in slow_controls:
        return 0.3   # 300ms - allow rendering
    else:
        return 0.1   # 100ms - conservative default

def get_optimal_typing_speed(text: str, control_type: str = None) -> float:
    """
    Return optimal typing interval based on text length and control type.
    
    Shorter intervals for automation, longer for human-like behavior when needed.
    """
    text_length = len(text)
    
    # For very short text (1-5 chars), use minimal interval
    if text_length <= 5:
        return 0.01  # 10ms - nearly instant
    
    # For medium text (6-20 chars), use fast interval  
    elif text_length <= 20:
        return 0.02  # 20ms - fast but stable
    
    # For long text (21+ chars), use moderate interval
    elif text_length <= 50:
        return 0.03  # 30ms - balance of speed and reliability
    
    # For very long text (51+ chars), use slower interval for stability
    else:
        return 0.05  # 50ms - slower but more reliable for long text

def get_type_optimization_for_control(control_type: str) -> dict:
    """
    Return optimization settings for different control types.
    """
    optimizations = {
        'EditControl': {
            'typing_speed': 'fast',      # Regular text fields
            'clear_method': 'select_all', # Ctrl+A then type
            'enter_behavior': 'none'     # Don't press enter unless requested
        },
        'ComboBoxControl': {
            'typing_speed': 'medium',    # Dropdowns may need time to respond
            'clear_method': 'select_all',
            'enter_behavior': 'none'
        },
        'PasswordControl': {
            'typing_speed': 'slow',      # Password fields need more time
            'clear_method': 'select_all',
            'enter_behavior': 'auto'     # Auto-press enter for login forms
        },
        'SearchControl': {
            'typing_speed': 'fast',
            'clear_method': 'select_all', 
            'enter_behavior': 'auto'     # Auto-press enter for search
        }
    }
    
    return optimizations.get(control_type, {
        'typing_speed': 'medium',
        'clear_method': 'select_all',
        'enter_behavior': 'none'
    })

@tool('Done Tool',args_schema=Done)
def done_tool(answer:str,desktop:Desktop=None):
    '''To indicate that the task is completed'''
    return answer

def get_optimal_launch_delay(app_name: str) -> float:
    """
    Return optimal delay for app launch operations.
    Faster polling for better responsiveness.
    """
    # Most apps load quickly, use shorter intervals
    return 0.15  # 150ms - much faster than 1000ms

def should_refresh_desktop_state(app_name: str, was_switch: bool) -> bool:
    """
    Determine if desktop state refresh is needed after launch.
    Skip refresh for simple switches to improve speed.
    """
    # Always refresh for new launches (need updated coordinates)
    if not was_switch:
        return True
    
    # For switches, only refresh if it's a complex app that might change UI
    complex_apps = {'chrome', 'firefox', 'edge', 'visual studio', 'photoshop', 'illustrator'}
    return app_name.lower() in complex_apps

@tool('Launch Tool',args_schema=Launch)
def launch_tool(name: str,desktop:Desktop=None) -> str:
    'Launch an application present in start menu (e.g., "notepad", "calculator", "chrome"). If already running, switches to existing window.'
    app_name,response,status=desktop.launch_app(name)
    if status!=0:
        return f'Failed to launch {name.title()}. {response}'
    else:
        # Check if this was a switch to existing app or a new launch
        was_switch = "already running" in response.lower()
        
        if was_switch:
            # App was already running and we switched to it
            pg.sleep(0.05)  # Reduced from 0.1s to 50ms
            
            # OPTIMIZATION: Conditional desktop refresh
            if should_refresh_desktop_state(app_name, was_switch):
                desktop.get_state(use_vision=False)
                return f'{name.title()} was already running. Switched to existing window. Desktop state refreshed. IMPORTANT: Use fresh coordinates from the updated desktop state for all subsequent actions.'
            else:
                return f'{name.title()} was already running. Switched to existing window. Ready for interaction.'
        else:
            # New app was launched, wait for it to load with optimized polling
            max_wait_time = 3.0  # Maximum 3 seconds total
            poll_interval = get_optimal_launch_delay(app_name)  # 150ms instead of 1000ms
            max_polls = int(max_wait_time / poll_interval)  # ~20 polls instead of 3
            
            for attempt in range(max_polls):
                if desktop.is_app_running(name):
                    # OPTIMIZATION: Early exit when app is detected
                    # Brief wait for app to stabilize, then refresh state
                    pg.sleep(0.2)  # Reduced from 1s to 200ms
                    desktop.get_state(use_vision=False)
                    return f'{name.title()} launched and desktop state refreshed. IMPORTANT: Use fresh coordinates from the updated desktop state for all subsequent actions.'
                
                pg.sleep(poll_interval)  # 150ms instead of 1000ms
            
            return f'Launching {name.title()}. App may still be loading - please wait a moment.'

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
def click_tool(loc:tuple[int,int],button:Literal['left','right','middle']='left',clicks:int=1,desktop:Desktop=None,control_type:str=None)->str:
    'Click on UI elements at specific coordinates. Supports left/right/middle mouse buttons and single/double/triple clicks.'
    x,y=loc
    
    # Validate coordinates are within screen bounds
    screen_width, screen_height = pg.size()
    if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
        return f'Error: Coordinates ({x},{y}) are outside screen bounds ({screen_width}x{screen_height})'
    
    # OPTIMIZATION: Direct click without cursor pre-positioning or redundant element detection
    # Trust the coordinates from desktop.get_state() - they're already precise
    pg.click(x=x, y=y, button=button, clicks=clicks)
    
    # OPTIMIZATION: Adaptive delay based on control type instead of fixed 1.0s
    delay = get_optimal_click_delay(control_type or 'Unknown')
    pg.sleep(delay)
    
    # Get element info for response (post-click is fine for reporting)
    try:
        control = desktop.get_element_under_cursor()
        element_name = control.Name or "Unknown"
        element_type = control.ControlTypeName
    except:
        element_name = "Unknown"
        element_type = control_type or "Unknown"
    
    num_clicks={1:'Single',2:'Double',3:'Triple'}
    return f'{num_clicks.get(clicks, "Multiple")} {button} click on {element_name} ({element_type}) at ({x},{y}).'

@tool('Type Tool',args_schema=Type)
def type_tool(loc:tuple[int,int],text:str,clear:Literal['true','false']='false',caret_position:Literal['start','idle','end']='idle',press_enter:Literal['true','false']='false',desktop:Desktop=None,control_type:str=None):
    'Type text into input fields, text areas, or focused elements. Set clear=True to replace existing text, False to append. Click on target element coordinates first and start typing.'
    x,y=loc
    
    # Validate coordinates are within screen bounds
    screen_width, screen_height = pg.size()
    if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
        return f'Error: Coordinates ({x},{y}) are outside screen bounds ({screen_width}x{screen_height})'
    
    # OPTIMIZATION: Direct click instead of HumanCursor for speed
    pg.click(x=x, y=y)
    pg.sleep(0.05)  # Brief delay for focus to settle
    
    # OPTIMIZATION: Batch key operations with minimal delays
    if clear == 'true':
        pg.hotkey('ctrl', 'a')  # Select all
        pg.sleep(0.02)          # Minimal delay
        pg.press('backspace')   # Clear
        pg.sleep(0.02)          # Minimal delay
    
    # Position caret efficiently
    if caret_position == 'start':
        pg.press('home')
        pg.sleep(0.01)
    elif caret_position == 'end':
        pg.press('end')
        pg.sleep(0.01)
    
    # OPTIMIZATION: Adaptive typing speed based on text length and control type
    interval = get_optimal_typing_speed(text, control_type)
    pg.typewrite(text, interval=interval)
    
    # Press enter if requested
    if press_enter == 'true':
        pg.sleep(0.02)  # Brief pause before enter
        pg.press('enter')
    
    # Get element info for response (post-typing is fine for reporting)
    try:
        control = desktop.get_element_under_cursor()
        element_name = control.Name or "Unknown"
        element_type = control.ControlTypeName
    except:
        element_name = "Unknown"
        element_type = control_type or "Unknown"
    
    return f'Typed "{text}" in {element_name} ({element_type}) at ({x},{y}).'

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
    return f"USER QUESTION: {question}\n\nPlease respond with your answer, and I'll continue based on your response."

@tool('System Tool',args_schema=System)
def system_tool(info_type:Literal['all','cpu','memory','disk','processes','summary']='all',desktop:Desktop=None)->str:
    '''Get comprehensive system information including CPU usage, memory stats, disk space, and top processes consuming resources. 
    Use 'all' for complete analysis, 'summary' for quick overview, or specify 'cpu', 'memory', 'disk', or 'processes' for specific info.'''
    import psutil
    import platform
    from datetime import datetime
    
    def bytes_to_gb(bytes_value):
        """Convert bytes to GB with 2 decimal places"""
        return round(bytes_value / (1024**3), 2)
    
    def get_cpu_info():
        """Get CPU information and usage"""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        
        info = f"CPU Information:\n"
        info += f"  Processor: {platform.processor()}\n"
        info += f"  Physical Cores: {cpu_count}\n"
        info += f"  Logical Cores (Threads): {cpu_threads}\n"
        info += f"  Overall Usage: {cpu_percent}%\n"
        
        if cpu_freq:
            info += f"  Current Frequency: {cpu_freq.current:.2f} MHz\n"
            info += f"  Max Frequency: {cpu_freq.max:.2f} MHz\n"
        
        info += f"  Per-Core Usage: {', '.join([f'Core {i}: {usage}%' for i, usage in enumerate(cpu_per_core)])}\n"
        
        return info
    
    def get_memory_info():
        """Get memory (RAM) information"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        info = f"Memory (RAM) Information:\n"
        info += f"  Total RAM: {bytes_to_gb(mem.total)} GB\n"
        info += f"  Available: {bytes_to_gb(mem.available)} GB\n"
        info += f"  Used: {bytes_to_gb(mem.used)} GB\n"
        info += f"  Usage: {mem.percent}%\n"
        info += f"  \n"
        info += f"  Swap/Page File:\n"
        info += f"    Total: {bytes_to_gb(swap.total)} GB\n"
        info += f"    Used: {bytes_to_gb(swap.used)} GB\n"
        info += f"    Usage: {swap.percent}%\n"
        
        return info
    
    def get_disk_info():
        """Get disk/storage information"""
        partitions = psutil.disk_partitions()
        
        info = f"Disk/Storage Information:\n"
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info += f"  Drive {partition.device}:\n"
                info += f"    File System: {partition.fstype}\n"
                info += f"    Total: {bytes_to_gb(usage.total)} GB\n"
                info += f"    Used: {bytes_to_gb(usage.used)} GB\n"
                info += f"    Free: {bytes_to_gb(usage.free)} GB\n"
                info += f"    Usage: {usage.percent}%\n"
            except PermissionError:
                continue
        
        return info
    
    def get_top_processes():
        """Get top processes by CPU and memory usage"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        top_cpu = sorted(processes, key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)[:5]
        
        # Sort by memory usage
        top_mem = sorted(processes, key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)[:5]
        
        info = f"Top Processes:\n\n"
        info += f"  Top 5 by CPU Usage:\n"
        for i, proc in enumerate(top_cpu, 1):
            cpu = proc.get('cpu_percent', 0) or 0
            mem = proc.get('memory_percent', 0) or 0
            mem_mb = bytes_to_gb(proc.get('memory_info', {}).rss if proc.get('memory_info') else 0) * 1024
            info += f"    {i}. {proc['name']} (PID: {proc['pid']})\n"
            info += f"       CPU: {cpu}% | Memory: {mem:.1f}% ({mem_mb:.0f} MB)\n"
        
        info += f"\n  Top 5 by Memory Usage:\n"
        for i, proc in enumerate(top_mem, 1):
            cpu = proc.get('cpu_percent', 0) or 0
            mem = proc.get('memory_percent', 0) or 0
            mem_mb = bytes_to_gb(proc.get('memory_info', {}).rss if proc.get('memory_info') else 0) * 1024
            info += f"    {i}. {proc['name']} (PID: {proc['pid']})\n"
            info += f"       Memory: {mem:.1f}% ({mem_mb:.0f} MB) | CPU: {cpu}%\n"
        
        return info
    
    def get_system_summary():
        """Get quick system summary"""
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        
        # Get main disk
        disk = psutil.disk_usage('C:\\')
        
        # Get top process
        top_proc = None
        max_cpu = 0
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                cpu = proc.info.get('cpu_percent', 0) or 0
                if cpu > max_cpu:
                    max_cpu = cpu
                    top_proc = proc.info['name']
            except:
                pass
        
        info = f"System Summary:\n"
        info += f"  OS: {platform.system()} {platform.release()} ({platform.version()})\n"
        info += f"  Computer: {platform.node()}\n"
        info += f"  CPU Usage: {cpu_percent}%\n"
        info += f"  Memory Usage: {mem.percent}% ({bytes_to_gb(mem.used)} GB / {bytes_to_gb(mem.total)} GB)\n"
        info += f"  Disk C: Usage: {disk.percent}% ({bytes_to_gb(disk.used)} GB / {bytes_to_gb(disk.total)} GB)\n"
        if top_proc:
            info += f"  Top Process: {top_proc} ({max_cpu}% CPU)\n"
        
        return info
    
    # Build response based on info_type
    try:
        result = f"System Analysis Report\n"
        result += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"{'='*60}\n\n"
        
        if info_type == 'all':
            result += get_system_summary() + "\n\n"
            result += get_cpu_info() + "\n"
            result += get_memory_info() + "\n"
            result += get_disk_info() + "\n"
            result += get_top_processes()
        elif info_type == 'summary':
            result += get_system_summary()
        elif info_type == 'cpu':
            result += get_cpu_info()
        elif info_type == 'memory':
            result += get_memory_info()
        elif info_type == 'disk':
            result += get_disk_info()
        elif info_type == 'processes':
            result += get_top_processes()
        else:
            result += get_system_summary()
        
        return result
        
    except Exception as e:
        return f"Error retrieving system information: {e}"

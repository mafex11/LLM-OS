from uiautomation import Control, GetRootControl, IsIconic, IsZoomed, IsWindowVisible, ControlType, ControlFromCursor, SetWindowTopmost, IsTopLevelWindow, ShowWindow, ControlFromHandle
from windows_use.desktop.config import EXCLUDED_APPS, BROWSER_NAMES
from windows_use.desktop.views import DesktopState,App,Size
from windows_use.tree.service import Tree
from PIL.Image import Image as PILImage
from contextlib import contextmanager
from fuzzywuzzy import process
from psutil import Process
from time import sleep
from io import BytesIO
from PIL import Image
import subprocess
import pyautogui
import ctypes
import base64
import csv
import io

class Desktop:
    def __init__(self):
        self.desktop_state=None
        self._screenshot_cache = None
        self._screenshot_cache_time = 0
        self._apps_cache = None
        self._apps_cache_time = 0
        self.cache_timeout = 2.0  # Cache screenshots and apps for 2 seconds
        
    def get_state(self,use_vision:bool=False, target_app:str=None)->DesktopState:
        tree=Tree(self)
        apps=self.get_apps()
        
        # Use precise detection if target_app is specified
        if target_app:
            tree_state=tree.get_precise_state(target_app)
        else:
            tree_state=tree.get_state()
            
        # Find the actual foreground app instead of assuming the first one
        active_app = self._get_foreground_app(apps)
        apps = [app for app in apps if app != active_app]
        if use_vision:
            # Capture full-screen screenshot for accurate coordinate mapping
            full_screenshot=self.get_screenshot(scale=1.0)
            screenshot=self.screenshot_in_bytes(full_screenshot)
        else:
            screenshot=None
        self.desktop_state=DesktopState(apps=apps,active_app=active_app,screenshot=screenshot,tree_state=tree_state)
        return self.desktop_state
    
    def get_window_element_from_element(self,element:Control)->Control|None:
        while element is not None:
            if IsTopLevelWindow(element.NativeWindowHandle):
                return element
            element = element.GetParentControl()
        return None
    
    def get_app_status(self,control:Control)->str:
        if IsIconic(control.NativeWindowHandle):
            return 'Minimized'
        elif IsZoomed(control.NativeWindowHandle):
            return 'Maximized'
        elif IsWindowVisible(control.NativeWindowHandle):
            return 'Normal'
        else:
            return 'Hidden'
    
    def get_cursor_location(self)->tuple[int,int]:
        position=pyautogui.position()
        return (position.x,position.y)
    
    def get_element_under_cursor(self)->Control:
        return ControlFromCursor()
    
    def get_apps_from_start_menu(self)->dict[str,str]:
        command='Get-StartApps | ConvertTo-Csv -NoTypeInformation'
        apps_info,_=self.execute_command(command)
        reader=csv.DictReader(io.StringIO(apps_info))
        return {row.get('Name').lower():row.get('AppID') for row in reader}
    
    def is_app_running(self,name:str)->bool:
        apps=self.get_apps()
        return process.extractOne(name,apps,score_cutoff=45) is not None
    
    def execute_command(self,command:str)->tuple[str,int]:
        try:
            result = subprocess.run(['powershell', '-Command']+command.split(), 
            capture_output=True, check=True)
            return (result.stdout.decode('latin1'),result.returncode)
        except subprocess.CalledProcessError as e:
            return (e.stdout.decode('latin1'),e.returncode)
        
    def is_app_browser(self,node:Control):
        process=Process(node.ProcessId)
        return process.name() in BROWSER_NAMES
    
    def get_default_language(self)->str:
        command="Get-Culture | Select-Object Name,DisplayName | ConvertTo-Csv -NoTypeInformation"
        response,_=self.execute_command(command)
        reader=csv.DictReader(io.StringIO(response))
        return "".join([row.get('DisplayName') for row in reader])
    
    def resize_app(self,name:str,size:tuple[int,int]=None,loc:tuple[int,int]=None)->tuple[str,int]:
        apps=self.get_apps()
        matched_app:tuple[App,int]|None=process.extractOne(name,apps)
        if matched_app is None:
            return (f'Application {name.title()} not found.',1)
        app,_=matched_app
        app_control=ControlFromHandle(app.handle)
        if loc is None:
            x=app_control.BoundingRectangle.left
            y=app_control.BoundingRectangle.top
            loc=(x,y)
        if size is None:
            width=app_control.BoundingRectangle.width()
            height=app_control.BoundingRectangle.height()
            size=(width,height)
        x,y=loc
        width,height=size
        app_control.MoveWindow(x,y,width,height)
        return (f'Application {name.title()} resized to {width}x{height} at {x},{y}.',0)
        
    def launch_app(self,name:str):
        # First check if the app is already running
        if self.is_app_running(name):
            # If it's running, switch to it instead of launching a new instance
            switch_result, switch_status = self.switch_app(name)
            if switch_status == 0:
                return (name, f'{name.title()} is already running. Switched to existing window.', 0)
            else:
                return (name, f'{name.title()} is running but failed to switch to it. {switch_result}', 1)
        
        # If not running, proceed with launching
        apps_map=self.get_apps_from_start_menu()
        matched_app=process.extractOne(name,apps_map.keys())
        if matched_app is None:
            return (f'Application {name.title()} not found in start menu.',1)
        app_name,_=matched_app
        appid=apps_map.get(app_name)
        if appid is None:
            return (name,f'Application {name.title()} not found in start menu.',1)
        if name.endswith('.exe'):
            response,status=self.execute_command(f'Start-Process "{appid}"')
        else:
            response,status=self.execute_command(f'Start-Process "shell:AppsFolder\\{appid}"')
        return app_name,response,status
    
    def switch_app(self,name:str):
        apps={app.name:app for app in self.desktop_state.apps}
        matched_app:tuple[str,float]=process.extractOne(name,list(apps.keys()))
        if matched_app is None:
            return (f'Application {name.title()} not found.',1)
        app_name,_=matched_app
        app=apps.get(app_name)
        if IsIconic(app.handle):
            ShowWindow(app.handle, cmdShow=9)
            return (f'{app_name.title()} restored from minimized state.',0)
        elif SetWindowTopmost(app.handle,isTopmost=True):
            return (f'{app_name.title()} switched to foreground.',0)
        else:
            return (f'Failed to switch to {app_name.title()}.',1)
    
    def get_app_size(self,control:Control):
        window=control.BoundingRectangle
        if window.isempty():
            return Size(width=0,height=0)
        return Size(width=window.width(),height=window.height())
    
    def is_app_visible(self,app)->bool:
        is_minimized=self.get_app_status(app)!='Minimized'
        size=self.get_app_size(app)
        area=size.width*size.height
        is_overlay=self.is_overlay_app(app)
        return not is_overlay and is_minimized and area>10
    
    def is_overlay_app(self,element:Control) -> bool:
        no_children = len(element.GetChildren()) == 0
        is_name = "Overlay" in element.Name.strip()
        return no_children or is_name
        
    def _get_foreground_app(self, apps: list[App]) -> App | None:
        """Get the actual foreground application using Windows API"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get the foreground window handle
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return apps[0] if apps else None
            
            # Get the process ID of the foreground window
            process_id = ctypes.wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            
            # Get the window title for debugging
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
                foreground_title = buffer.value
            else:
                foreground_title = "Unknown"
            
            # Find the app that matches this process ID
            for app in apps:
                try:
                    # Get process ID from the app's window handle
                    app_process_id = ctypes.wintypes.DWORD()
                    ctypes.windll.user32.GetWindowThreadProcessId(app.handle, ctypes.byref(app_process_id))
                    
                    if app_process_id.value == process_id.value:
                        return app
                except:
                    continue
            
            # If no match found, return the first app as fallback
            return apps[0] if apps else None
            
        except Exception as e:
            # Fallback to first app if there's any error
            return apps[0] if apps else None

    def get_apps(self) -> list[App]:
        import time
        current_time = time.time()
        
        # Check if we have cached apps that are still valid
        if (self._apps_cache is not None and 
            current_time - self._apps_cache_time < self.cache_timeout):
            return self._apps_cache
        
        try:
            sleep(0.2)  # Reduced from 0.5 to 0.2 seconds
            desktop = GetRootControl()  # Get the desktop control
            elements = desktop.GetChildren()
            apps = []
            for depth, element in enumerate(elements):
                if element.ClassName in EXCLUDED_APPS or self.is_overlay_app(element):
                    continue
                if element.ControlType in [ControlType.WindowControl, ControlType.PaneControl]:
                    status = self.get_app_status(element)
                    size=self.get_app_size(element)
                    apps.append(App(name=element.Name, depth=depth, status=status,size=size,handle=element.NativeWindowHandle))
        except Exception as ex:
            print(f"Error: {ex}")
            apps = []
        
        # Cache the apps
        self._apps_cache = apps
        self._apps_cache_time = current_time
        
        return apps
    
    def get_dpi_scaling():
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        dpi = user32.GetDpiForSystem()
        return dpi / 96.0
    
    def screenshot_in_bytes(self,screenshot:PILImage)->bytes:
        buffer=BytesIO()
        # Use JPEG with quality 85 for faster processing and smaller size
        screenshot.save(buffer, format='JPEG', quality=85, optimize=True)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{img_base64}"
        return data_uri

    def get_screenshot(self,scale:float=0.7)->Image.Image:
        import time
        current_time = time.time()
        
        # Check if we have a cached screenshot that's still valid
        if (self._screenshot_cache is not None and 
            current_time - self._screenshot_cache_time < self.cache_timeout):
            return self._screenshot_cache
        
        # Take new screenshot
        screenshot=pyautogui.screenshot()
        
        # Only scale if scale != 1.0 to avoid unnecessary processing
        if scale != 1.0:
            size=(int(screenshot.width*scale), int(screenshot.height*scale))
            screenshot.thumbnail(size=size, resample=Image.Resampling.LANCZOS)
        
        # Cache the screenshot
        self._screenshot_cache = screenshot
        self._screenshot_cache_time = current_time
        
        return screenshot
    
    def clear_cache(self):
        """Clear all cached data to force fresh state"""
        self._screenshot_cache = None
        self._screenshot_cache_time = 0
        self._apps_cache = None
        self._apps_cache_time = 0
        if hasattr(self, '_last_state_time'):
            delattr(self, '_last_state_time')
    
    @contextmanager
    def auto_minimize(self):
        SW_MINIMIZE=6
        SW_RESTORE = 9
        try:
            user32 = ctypes.windll.user32
            hWnd = user32.GetForegroundWindow()
            user32.ShowWindow(hWnd, SW_MINIMIZE)
            yield
        finally:
            user32.ShowWindow(hWnd, SW_RESTORE)
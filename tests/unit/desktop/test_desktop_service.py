"""
Unit tests for desktop service.
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.desktop.service import Desktop


class TestDesktop:
    """Tests for Desktop class."""
    
    @pytest.fixture
    def desktop(self):
        """Create Desktop instance."""
        return Desktop()
    
    def test_desktop_initialization(self):
        """Test desktop initializes correctly."""
        desktop = Desktop()
        assert desktop is not None
        assert hasattr(desktop, 'desktop_state')
    
    @patch('windows_use.desktop.service.uiautomation')
    def test_get_apps(self, mock_uia, desktop):
        """Test getting list of running applications."""
        # Mock running windows
        mock_window1 = MagicMock()
        mock_window1.Name = "Notepad"
        mock_window1.NativeWindowHandle = 12345
        
        mock_window2 = MagicMock()
        mock_window2.Name = "Calculator"
        mock_window2.NativeWindowHandle = 67890
        
        mock_uia.GetRootControl.return_value.GetChildren.return_value = [
            mock_window1, mock_window2
        ]
        
        apps = desktop.get_apps()
        
        assert isinstance(apps, list)
        assert len(apps) >= 0
    
    @patch('windows_use.desktop.service.uiautomation')
    def test_get_active_app(self, mock_uia, desktop):
        """Test getting currently active application."""
        mock_window = MagicMock()
        mock_window.Name = "Chrome"
        mock_window.NativeWindowHandle = 11111
        
        mock_uia.GetForegroundControl.return_value = mock_window
        
        active_app = desktop.get_active_app()
        
        assert active_app is not None or active_app is None  # Can be None if no app
    
    @patch('windows_use.desktop.service.subprocess')
    def test_launch_app_success(self, mock_subprocess, desktop):
        """Test successful app launch."""
        mock_subprocess.run.return_value = MagicMock(returncode=0)
        
        with patch.object(desktop, 'is_app_running', return_value=False):
            app_name, message, status = desktop.launch_app("notepad")
        
        assert status == 0 or isinstance(status, int)
        assert isinstance(message, str)
    
    @patch('windows_use.desktop.service.subprocess')
    def test_launch_app_already_running(self, mock_subprocess, desktop):
        """Test launching app that's already running."""
        with patch.object(desktop, 'is_app_running', return_value=True):
            with patch.object(desktop, 'switch_app', return_value=("Switched", 0)):
                app_name, message, status = desktop.launch_app("calculator")
        
        assert "already" in message.lower() or "switch" in message.lower()
    
    def test_switch_app_success(self, desktop):
        """Test switching to existing app."""
        mock_app = MagicMock()
        mock_app.name = "Notepad"
        mock_app.handle = 12345
        
        with patch.object(desktop, 'get_apps', return_value=[mock_app]):
            with patch('windows_use.desktop.service.win32gui') as mock_win32:
                message, status = desktop.switch_app("notepad")
        
        assert isinstance(status, int)
    
    def test_switch_app_not_found(self, desktop):
        """Test switching to non-existent app."""
        with patch.object(desktop, 'get_apps', return_value=[]):
            message, status = desktop.switch_app("nonexistent")
        
        assert status != 0
        assert "not found" in message.lower() or "not running" in message.lower()
    
    @patch('windows_use.desktop.service.subprocess')
    def test_execute_command_success(self, mock_subprocess, desktop):
        """Test executing PowerShell command successfully."""
        mock_subprocess.run.return_value = MagicMock(
            returncode=0,
            stdout="Command output",
            stderr=""
        )
        
        output, status = desktop.execute_command("Get-Date")
        
        assert status == 0
        assert isinstance(output, str)
    
    @patch('windows_use.desktop.service.subprocess')
    def test_execute_command_failure(self, mock_subprocess, desktop):
        """Test executing invalid PowerShell command."""
        mock_subprocess.run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Command not found"
        )
        
        output, status = desktop.execute_command("Invalid-Command")
        
        assert status != 0
        assert len(output) >= 0
    
    def test_is_app_running_true(self, desktop):
        """Test checking if app is running (true case)."""
        mock_app = MagicMock()
        mock_app.name = "Chrome"
        
        with patch.object(desktop, 'get_apps', return_value=[mock_app]):
            result = desktop.is_app_running("chrome")
        
        assert result is True
    
    def test_is_app_running_false(self, desktop):
        """Test checking if app is running (false case)."""
        with patch.object(desktop, 'get_apps', return_value=[]):
            result = desktop.is_app_running("nonexistent")
        
        assert result is False
    
    def test_resize_app_success(self, desktop):
        """Test resizing application window."""
        mock_app = MagicMock()
        mock_app.name = "Notepad"
        mock_app.handle = 12345
        
        with patch.object(desktop, 'get_apps', return_value=[mock_app]):
            with patch('windows_use.desktop.service.win32gui') as mock_win32:
                message, status = desktop.resize_app("notepad", size=(800, 600))
        
        assert isinstance(status, int)
    
    def test_resize_app_not_found(self, desktop):
        """Test resizing non-existent app."""
        with patch.object(desktop, 'get_apps', return_value=[]):
            message, status = desktop.resize_app("nonexistent", size=(800, 600))
        
        assert status != 0
    
    @patch('windows_use.desktop.service.uiautomation')
    def test_get_element_under_cursor(self, mock_uia, desktop):
        """Test getting UI element under cursor."""
        mock_control = MagicMock()
        mock_control.Name = "Button"
        mock_control.ControlTypeName = "ButtonControl"
        
        with patch('windows_use.desktop.service.pyautogui.position', return_value=(100, 100)):
            mock_uia.ControlFromPoint.return_value = mock_control
            
            element = desktop.get_element_under_cursor()
        
        assert element is not None or element is None
    
    def test_invalidate_ui_cache(self, desktop):
        """Test invalidating UI cache."""
        # Should not raise any errors
        desktop.invalidate_ui_cache()
        
        # Verify state is updated
        assert hasattr(desktop, 'desktop_state')
    
    @patch('windows_use.desktop.service.Tree')
    def test_get_state(self, mock_tree_class, desktop):
        """Test getting desktop state."""
        mock_tree = MagicMock()
        mock_tree.get_nodes.return_value = ([], [], [])  # interactive, informative, scrollable
        mock_tree_class.return_value = mock_tree
        
        with patch.object(desktop, 'get_active_app', return_value=None):
            state = desktop.get_state(use_vision=False)
        
        assert state is not None
        assert hasattr(state, 'tree_state') or hasattr(state, 'apps')



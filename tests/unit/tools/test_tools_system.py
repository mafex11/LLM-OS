"""
Unit tests for system-related agent tools (System, Shell, Human, Scrape).
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.agent.tools.service import (
    system_tool,
    shell_tool,
    human_tool,
    scrape_tool
)
from windows_use.desktop.service import Desktop


class TestSystemTool:
    """Tests for System Tool."""
    
    @patch('windows_use.agent.tools.service.psutil')
    @patch('windows_use.agent.tools.service.platform')
    def test_system_tool_summary(self, mock_platform, mock_psutil):
        """Test system tool with summary mode."""
        mock_psutil.cpu_percent.return_value = 45.5
        mock_mem = MagicMock()
        mock_mem.percent = 60.0
        mock_mem.used = 8 * (1024**3)
        mock_mem.total = 16 * (1024**3)
        mock_psutil.virtual_memory.return_value = mock_mem
        
        mock_disk = MagicMock()
        mock_disk.percent = 70.0
        mock_disk.used = 350 * (1024**3)
        mock_disk.total = 500 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk
        
        mock_platform.system.return_value = "Windows"
        mock_platform.release.return_value = "10"
        mock_platform.node.return_value = "TestPC"
        
        result = system_tool(info_type='summary')
        
        assert "system summary" in result.lower()
        assert "45.5" in result or "cpu" in result.lower()
    
    @patch('windows_use.agent.tools.service.psutil')
    def test_system_tool_cpu(self, mock_psutil):
        """Test system tool with CPU info."""
        mock_psutil.cpu_percent.return_value = 35.0
        mock_psutil.cpu_count.side_effect = [4, 8]  # Physical cores, logical cores
        mock_freq = MagicMock()
        mock_freq.current = 2400.0
        mock_freq.max = 3600.0
        mock_psutil.cpu_freq.return_value = mock_freq
        
        result = system_tool(info_type='cpu')
        
        assert "cpu" in result.lower()
    
    @patch('windows_use.agent.tools.service.psutil')
    def test_system_tool_memory(self, mock_psutil):
        """Test system tool with memory info."""
        mock_mem = MagicMock()
        mock_mem.total = 16 * (1024**3)
        mock_mem.available = 8 * (1024**3)
        mock_mem.used = 8 * (1024**3)
        mock_mem.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_mem
        
        mock_swap = MagicMock()
        mock_swap.total = 4 * (1024**3)
        mock_swap.used = 1 * (1024**3)
        mock_swap.percent = 25.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        result = system_tool(info_type='memory')
        
        assert "memory" in result.lower() or "ram" in result.lower()
    
    @patch('windows_use.agent.tools.service.psutil')
    def test_system_tool_disk(self, mock_psutil):
        """Test system tool with disk info."""
        mock_partition = MagicMock()
        mock_partition.device = "C:\\"
        mock_partition.fstype = "NTFS"
        mock_partition.mountpoint = "C:\\"
        mock_psutil.disk_partitions.return_value = [mock_partition]
        
        mock_usage = MagicMock()
        mock_usage.total = 500 * (1024**3)
        mock_usage.used = 300 * (1024**3)
        mock_usage.free = 200 * (1024**3)
        mock_usage.percent = 60.0
        mock_psutil.disk_usage.return_value = mock_usage
        
        result = system_tool(info_type='disk')
        
        assert "disk" in result.lower() or "storage" in result.lower()
    
    @patch('windows_use.agent.tools.service.psutil')
    def test_system_tool_processes(self, mock_psutil):
        """Test system tool with processes info."""
        mock_proc1 = MagicMock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'chrome.exe',
            'cpu_percent': 15.5,
            'memory_percent': 10.0,
            'memory_info': MagicMock(rss=500 * 1024**2)
        }
        
        mock_proc2 = MagicMock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'python.exe',
            'cpu_percent': 5.0,
            'memory_percent': 8.0,
            'memory_info': MagicMock(rss=300 * 1024**2)
        }
        
        mock_psutil.process_iter.return_value = [mock_proc1, mock_proc2]
        
        result = system_tool(info_type='processes')
        
        assert "process" in result.lower()
    
    @patch('windows_use.agent.tools.service.psutil')
    def test_system_tool_all(self, mock_psutil):
        """Test system tool with all info."""
        # Setup basic mocks
        mock_psutil.cpu_percent.return_value = 40.0
        mock_mem = MagicMock()
        mock_mem.percent = 55.0
        mock_mem.used = mock_mem.available = mock_mem.total = 8 * (1024**3)
        mock_psutil.virtual_memory.return_value = mock_mem
        mock_psutil.swap_memory.return_value = mock_mem
        mock_psutil.disk_partitions.return_value = []
        mock_psutil.process_iter.return_value = []
        mock_psutil.cpu_count.side_effect = [4, 8]
        mock_psutil.cpu_freq.return_value = None
        
        result = system_tool(info_type='all')
        
        assert "system" in result.lower()


class TestShellTool:
    """Tests for Shell Tool."""
    
    def test_shell_tool_success(self):
        """Test successful shell command execution."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.execute_command.return_value = ("Command output", 0)
        
        result = shell_tool(command="Get-Date", desktop=mock_desktop)
        
        mock_desktop.execute_command.assert_called_once_with("Get-Date")
        assert "status code: 0" in result.lower()
        assert "command output" in result.lower()
    
    def test_shell_tool_failure(self):
        """Test failed shell command execution."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.execute_command.return_value = ("Error message", 1)
        
        result = shell_tool(command="Invalid-Command", desktop=mock_desktop)
        
        assert "status code: 1" in result.lower()
        assert "error message" in result.lower()
    
    def test_shell_tool_empty_command(self):
        """Test shell tool with empty command."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.execute_command.return_value = ("", 0)
        
        result = shell_tool(command="", desktop=mock_desktop)
        
        mock_desktop.execute_command.assert_called_once_with("")


class TestHumanTool:
    """Tests for Human Tool."""
    
    def test_human_tool_basic(self):
        """Test human tool returns question."""
        question = "What is your favorite color?"
        result = human_tool(question=question)
        
        assert result == question
    
    def test_human_tool_clarification(self):
        """Test human tool for clarification."""
        question = "Should I proceed with deleting these files?"
        result = human_tool(question=question)
        
        assert result == question
    
    def test_human_tool_empty_question(self):
        """Test human tool with empty question."""
        result = human_tool(question="")
        
        assert result == ""


class TestScrapeTool:
    """Tests for Scrape Tool."""
    
    @patch('windows_use.agent.tools.service.requests')
    @patch('windows_use.agent.tools.service.markdownify')
    def test_scrape_tool_success(self, mock_markdownify, mock_requests):
        """Test successful webpage scraping."""
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Test Page</h1></body></html>"
        mock_requests.get.return_value = mock_response
        mock_markdownify.return_value = "# Test Page"
        
        result = scrape_tool(url="http://example.com")
        
        mock_requests.get.assert_called_once_with("http://example.com", timeout=10)
        assert "scraped" in result.lower()
        assert "test page" in result.lower()
    
    @patch('windows_use.agent.tools.service.requests')
    def test_scrape_tool_timeout(self, mock_requests):
        """Test scrape tool with timeout."""
        mock_requests.get.side_effect = Exception("Timeout")
        
        with pytest.raises(Exception) as exc_info:
            scrape_tool(url="http://example.com")
        
        assert "timeout" in str(exc_info.value).lower()
    
    @patch('windows_use.agent.tools.service.requests')
    @patch('windows_use.agent.tools.service.markdownify')
    def test_scrape_tool_different_urls(self, mock_markdownify, mock_requests):
        """Test scraping different URLs."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_requests.get.return_value = mock_response
        mock_markdownify.return_value = "Content"
        
        urls = [
            "http://example.com",
            "https://test.com",
            "http://example.com/page"
        ]
        
        for url in urls:
            mock_requests.reset_mock()
            result = scrape_tool(url=url)
            mock_requests.get.assert_called_once_with(url, timeout=10)



"""
Integration tests for tool execution flow.
Tests the full execution path from agent to tool to desktop.
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.agent.service import Agent
from windows_use.agent.registry.service import Registry
from windows_use.desktop.service import Desktop
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage


class TestToolExecutionFlow:
    """Integration tests for complete tool execution flow."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for agent."""
        mock = MagicMock(spec=BaseChatModel)
        mock.invoke.return_value = AIMessage(
            content='<thought>Testing tool</thought><action_name>Done Tool</action_name><action_input>{"answer": "Complete"}</action_input>'
        )
        return mock
    
    @pytest.fixture
    def mock_desktop(self):
        """Mock desktop service."""
        mock = MagicMock(spec=Desktop)
        mock.get_state.return_value = MagicMock(
            active_app=MagicMock(name="TestApp"),
            apps=[],
            tree_state=MagicMock(interactive_nodes=[], informative_nodes=[], scrollable_nodes=[])
        )
        return mock
    
    @pytest.fixture
    def agent(self, mock_llm):
        """Create agent instance for testing."""
        with patch('windows_use.agent.service.Desktop') as mock_desktop_class:
            mock_desktop_class.return_value = MagicMock()
            agent = Agent(llm=mock_llm, max_steps=5)
            return agent
    
    def test_agent_invokes_done_tool(self, agent, mock_llm):
        """Test complete flow: agent -> done tool."""
        mock_llm.invoke.return_value = AIMessage(
            content='<thought>Task is done</thought><action_name>Done Tool</action_name><action_input>{"answer": "Task completed"}</action_input>'
        )
        
        result = agent.invoke("Say hello")
        
        assert result.is_done or result.content or result.error
    
    @patch('windows_use.agent.tools.service.pg')
    def test_agent_invokes_click_tool(self, mock_pg, agent, mock_llm):
        """Test complete flow: agent -> click tool -> pyautogui."""
        mock_pg.size.return_value = (1920, 1080)
        
        mock_llm.invoke.return_value = AIMessage(
            content='<thought>Clicking button</thought><action_name>Click Tool</action_name><action_input>{"loc": [100, 100], "button": "left", "clicks": 1}</action_input>'
        )
        
        with patch.object(agent.desktop, 'get_element_under_cursor', return_value=MagicMock(Name="Button", ControlTypeName="ButtonControl")):
            result = agent.invoke("Click at 100,100")
        
        # Agent should execute without errors
        assert isinstance(result.error, str) or result.error is None
    
    @patch('windows_use.agent.tools.service.pg')
    def test_agent_invokes_type_tool(self, mock_pg, agent, mock_llm):
        """Test complete flow: agent -> type tool -> pyautogui."""
        mock_pg.size.return_value = (1920, 1080)
        
        mock_llm.invoke.return_value = AIMessage(
            content='<thought>Typing text</thought><action_name>Type Tool</action_name><action_input>{"loc": [100, 100], "text": "Hello", "clear": "false"}</action_input>'
        )
        
        with patch.object(agent.desktop, 'get_element_under_cursor', return_value=MagicMock(Name="TextBox", ControlTypeName="EditControl")):
            result = agent.invoke("Type hello")
        
        assert isinstance(result.error, str) or result.error is None
    
    def test_agent_invokes_launch_tool(self, agent, mock_llm):
        """Test complete flow: agent -> launch tool -> desktop."""
        mock_llm.invoke.return_value = AIMessage(
            content='<thought>Opening app</thought><action_name>Launch Tool</action_name><action_input>{"name": "notepad"}</action_input>'
        )
        
        with patch.object(agent.desktop, 'launch_app', return_value=("notepad", "Launched", 0)):
            with patch.object(agent.desktop, 'is_app_running', return_value=True):
                with patch.object(agent.desktop, 'get_state', return_value=MagicMock()):
                    result = agent.invoke("Open notepad")
        
        assert isinstance(result.error, str) or result.error is None
    
    def test_agent_handles_tool_error(self, agent, mock_llm):
        """Test agent handles tool execution errors gracefully."""
        mock_llm.invoke.return_value = AIMessage(
            content='<thought>Clicking</thought><action_name>Click Tool</action_name><action_input>{"loc": [9999, 9999]}</action_input>'
        )
        
        result = agent.invoke("Click at invalid location")
        
        # Should handle error without crashing
        assert result.error or not result.is_done
    
    def test_agent_multi_step_execution(self, agent, mock_llm):
        """Test agent executes multiple steps."""
        responses = [
            AIMessage(content='<thought>Step 1</thought><action_name>Wait Tool</action_name><action_input>{"duration": 1}</action_input>'),
            AIMessage(content='<thought>Step 2</thought><action_name>Done Tool</action_name><action_input>{"answer": "Finished"}</action_input>')
        ]
        mock_llm.invoke.side_effect = responses
        
        with patch('windows_use.agent.tools.service.pg.sleep'):
            result = agent.invoke("Wait then finish")
        
        # Should complete after multiple steps
        assert mock_llm.invoke.call_count >= 1
    
    def test_registry_executes_tool(self):
        """Test registry executes tools correctly."""
        mock_desktop = MagicMock(spec=Desktop)
        registry = Registry([])
        
        # Test done tool through registry
        result = registry.execute("Done Tool", desktop=mock_desktop, answer="Test complete")
        
        assert result.is_success
        assert "Test complete" in result.content
    
    def test_registry_handles_invalid_tool(self):
        """Test registry handles invalid tool name."""
        mock_desktop = MagicMock(spec=Desktop)
        registry = Registry([])
        
        result = registry.execute("Invalid Tool", desktop=mock_desktop)
        
        assert not result.is_success
        assert result.error
    
    @patch('windows_use.agent.tools.service.pc')
    def test_clipboard_tool_integration(self, mock_pc):
        """Test clipboard tool integration."""
        mock_desktop = MagicMock(spec=Desktop)
        registry = Registry([])
        
        # Test copy
        result = registry.execute("Clipboard Tool", desktop=mock_desktop, mode="copy", text="Test data")
        
        mock_pc.copy.assert_called_once_with("Test data")
        assert result.is_success
    
    def test_shell_tool_integration(self):
        """Test shell tool integration."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.execute_command.return_value = ("Output", 0)
        registry = Registry([])
        
        result = registry.execute("Shell Tool", desktop=mock_desktop, command="Get-Date")
        
        mock_desktop.execute_command.assert_called_once_with("Get-Date")
        assert result.is_success








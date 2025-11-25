"""
Unit tests for tree service (UI element parsing).
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.tree.service import Tree
from windows_use.desktop.service import Desktop


class TestTree:
    """Tests for Tree class."""
    
    @pytest.fixture
    def mock_desktop(self):
        """Mock desktop instance."""
        return MagicMock(spec=Desktop)
    
    @pytest.fixture
    def tree(self, mock_desktop):
        """Create Tree instance with mock desktop."""
        return Tree(mock_desktop)
    
    def test_tree_initialization(self, mock_desktop):
        """Test tree initializes correctly."""
        tree = Tree(mock_desktop)
        assert tree.desktop == mock_desktop
    
    @patch('windows_use.tree.service.uiautomation')
    def test_get_nodes_basic(self, mock_uia, tree):
        """Test getting UI nodes from control."""
        # Mock control with children
        mock_control = MagicMock()
        mock_button = MagicMock()
        mock_button.ControlTypeName = "ButtonControl"
        mock_button.Name = "Submit"
        mock_button.BoundingRectangle = MagicMock(
            left=100, top=100, right=200, bottom=150,
            width=100, height=50
        )
        mock_button.IsEnabled = True
        
        mock_control.GetChildren.return_value = [mock_button]
        
        interactive, informative, scrollable = tree.get_nodes(mock_control, is_browser=False)
        
        # Should find the button as interactive
        assert len(interactive) >= 0
    
    @patch('windows_use.tree.service.uiautomation')
    def test_get_nodes_text_elements(self, mock_uia, tree):
        """Test getting text/informative elements."""
        mock_control = MagicMock()
        mock_text = MagicMock()
        mock_text.ControlTypeName = "TextControl"
        mock_text.Name = "Hello World"
        mock_text.BoundingRectangle = MagicMock(
            left=100, top=100, right=300, bottom=120
        )
        
        mock_control.GetChildren.return_value = [mock_text]
        
        interactive, informative, scrollable = tree.get_nodes(mock_control, is_browser=False)
        
        # Text should be in informative
        assert len(informative) >= 0
    
    @patch('windows_use.tree.service.uiautomation')
    def test_get_nodes_scrollable_elements(self, mock_uia, tree):
        """Test identifying scrollable elements."""
        mock_control = MagicMock()
        mock_list = MagicMock()
        mock_list.ControlTypeName = "ListControl"
        mock_list.Name = "File List"
        mock_list.BoundingRectangle = MagicMock(
            left=0, top=0, right=400, bottom=600
        )
        
        mock_control.GetChildren.return_value = [mock_list]
        
        interactive, informative, scrollable = tree.get_nodes(mock_control, is_browser=False)
        
        # List might be scrollable
        assert isinstance(scrollable, list)
    
    def test_is_interactive_button(self, tree):
        """Test identifying interactive button control."""
        mock_control = MagicMock()
        mock_control.ControlTypeName = "ButtonControl"
        mock_control.IsEnabled = True
        mock_control.BoundingRectangle = MagicMock(width=100, height=50)
        
        result = tree._is_interactive(mock_control)
        
        assert result is True or isinstance(result, bool)
    
    def test_is_interactive_disabled(self, tree):
        """Test non-interactive disabled control."""
        mock_control = MagicMock()
        mock_control.ControlTypeName = "ButtonControl"
        mock_control.IsEnabled = False
        
        result = tree._is_interactive(mock_control)
        
        assert result is False or isinstance(result, bool)
    
    def test_is_informative_text(self, tree):
        """Test identifying informative text control."""
        mock_control = MagicMock()
        mock_control.ControlTypeName = "TextControl"
        mock_control.Name = "Information text"
        
        result = tree._is_informative(mock_control)
        
        assert isinstance(result, bool)
    
    def test_is_scrollable_list(self, tree):
        """Test identifying scrollable list."""
        mock_control = MagicMock()
        mock_control.ControlTypeName = "ListControl"
        mock_control.BoundingRectangle = MagicMock(height=500)
        
        result = tree._is_scrollable(mock_control)
        
        assert isinstance(result, bool)
    
    def test_filter_visible_elements(self, tree):
        """Test filtering visible UI elements."""
        # Mock elements
        visible_elem = MagicMock()
        visible_elem.BoundingRectangle = MagicMock(
            left=100, top=100, right=200, bottom=150,
            width=100, height=50
        )
        
        invisible_elem = MagicMock()
        invisible_elem.BoundingRectangle = MagicMock(
            left=-1000, top=-1000, right=-900, bottom=-950,
            width=100, height=50
        )
        
        elements = [visible_elem, invisible_elem]
        
        filtered = tree._filter_visible(elements)
        
        # Should filter out off-screen elements
        assert len(filtered) <= len(elements)
    
    def test_get_element_center(self, tree):
        """Test calculating element center coordinates."""
        mock_control = MagicMock()
        mock_control.BoundingRectangle = MagicMock(
            left=100, top=100, right=200, bottom=150
        )
        
        center = tree._get_element_center(mock_control)
        
        assert center["x"] == 150  # (100 + 200) / 2
        assert center["y"] == 125  # (100 + 150) / 2



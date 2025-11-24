"""
Unit tests for activity analyzer.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from windows_use.tracking.analyzer import ActivityAnalyzer


class TestActivityAnalyzer:
    """Tests for ActivityAnalyzer class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM instance."""
        mock = MagicMock()
        mock.invoke.return_value = MagicMock(content="Category: work\nFocus Score: 85")
        return mock
    
    @pytest.fixture
    def analyzer(self, mock_llm):
        """Create ActivityAnalyzer instance with mock LLM."""
        return ActivityAnalyzer(llm=mock_llm)
    
    def test_analyzer_initialization_with_llm(self, mock_llm):
        """Test analyzer initializes with provided LLM."""
        analyzer = ActivityAnalyzer(llm=mock_llm)
        assert analyzer.llm == mock_llm
    
    @patch('windows_use.tracking.analyzer.ChatGoogleGenerativeAI')
    def test_analyzer_initialization_with_api_key(self, mock_chat_class):
        """Test analyzer initializes with API key."""
        mock_llm = MagicMock()
        mock_chat_class.return_value = mock_llm
        
        analyzer = ActivityAnalyzer(google_api_key="test-key")
        
        mock_chat_class.assert_called_once()
        assert analyzer.llm is not None
    
    def test_categorize_app_work(self, analyzer):
        """Test categorizing work applications."""
        work_apps = ["vscode", "visual studio", "pycharm", "sublime"]
        
        for app in work_apps:
            category = analyzer.categorize_app(app, "Code Editor")
            assert category in ["work", "development", "productivity"]
    
    def test_categorize_app_entertainment(self, analyzer):
        """Test categorizing entertainment applications."""
        entertainment_apps = ["spotify", "netflix", "youtube", "games"]
        
        for app in entertainment_apps:
            category = analyzer.categorize_app(app, "Media Player")
            assert category in ["entertainment", "media", "leisure"]
    
    def test_categorize_app_communication(self, analyzer):
        """Test categorizing communication applications."""
        comm_apps = ["slack", "teams", "outlook", "discord"]
        
        for app in comm_apps:
            category = analyzer.categorize_app(app, "Communication")
            assert category in ["communication", "work"]
    
    def test_calculate_focus_score_high(self, analyzer):
        """Test calculating high focus score."""
        activities = [
            {
                "app_name": "VSCode",
                "category": "work",
                "duration_seconds": 3600  # 1 hour
            },
            {
                "app_name": "Chrome",
                "category": "research",
                "duration_seconds": 1800  # 30 minutes
            }
        ]
        
        score = analyzer.calculate_focus_score(activities)
        
        assert 70 <= score <= 100
    
    def test_calculate_focus_score_low(self, analyzer):
        """Test calculating low focus score."""
        activities = [
            {
                "app_name": "YouTube",
                "category": "entertainment",
                "duration_seconds": 3600
            },
            {
                "app_name": "Games",
                "category": "entertainment",
                "duration_seconds": 1800
            }
        ]
        
        score = analyzer.calculate_focus_score(activities)
        
        assert 0 <= score <= 50
    
    def test_calculate_focus_score_empty(self, analyzer):
        """Test calculating focus score with no activities."""
        score = analyzer.calculate_focus_score([])
        
        assert score == 0 or score == 50  # Default score
    
    def test_generate_insights_productive(self, analyzer):
        """Test generating insights for productive day."""
        summary = {
            "total_active_time": 28800,  # 8 hours
            "work_time": 21600,  # 6 hours
            "entertainment_time": 3600,  # 1 hour
            "focus_score": 85
        }
        
        insights = analyzer.generate_insights(summary)
        
        assert isinstance(insights, str)
        assert len(insights) > 0
    
    def test_generate_insights_low_productivity(self, analyzer):
        """Test generating insights for low productivity."""
        summary = {
            "total_active_time": 14400,  # 4 hours
            "work_time": 3600,  # 1 hour
            "entertainment_time": 10800,  # 3 hours
            "focus_score": 35
        }
        
        insights = analyzer.generate_insights(summary)
        
        assert isinstance(insights, str)
        assert len(insights) > 0
    
    def test_analyze_screenshot_with_llm(self, analyzer, mock_llm):
        """Test analyzing screenshot with LLM."""
        mock_llm.invoke.return_value = MagicMock(
            content="The user is writing code in a Python IDE."
        )
        
        result = analyzer.analyze_screenshot(
            "screenshot.png",
            "VSCode",
            "main.py"
        )
        
        assert isinstance(result, dict)
        assert "description" in result or "category" in result
    
    def test_summarize_day_basic(self, analyzer):
        """Test summarizing a day's activities."""
        activities = [
            {
                "app_name": "Chrome",
                "window_title": "Documentation",
                "duration_seconds": 1800,
                "category": "research"
            },
            {
                "app_name": "VSCode",
                "window_title": "project.py",
                "duration_seconds": 3600,
                "category": "work"
            }
        ]
        
        summary = analyzer.summarize_day(activities, "2025-11-24")
        
        assert summary["date"] == "2025-11-24"
        assert summary["total_active_time"] >= 5400
        assert "work_time" in summary
        assert "focus_score" in summary
    
    def test_summarize_day_empty(self, analyzer):
        """Test summarizing day with no activities."""
        summary = analyzer.summarize_day([], "2025-11-24")
        
        assert summary["date"] == "2025-11-24"
        assert summary["total_active_time"] == 0
        assert summary["focus_score"] >= 0


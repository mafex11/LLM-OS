"""
Comprehensive test cases for Windows-Use Agent
"""
import time
from typing import Dict, Any, List
from windows_use.agent import Agent
from windows_use.agent.registry.service import Registry
from windows_use.desktop.service import Desktop
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from .test_logger import TestLogger, TestResult

class AgentTestCases:
    def __init__(self, agent: Agent, test_logger: TestLogger):
        self.agent = agent
        self.logger = test_logger
        self.desktop = agent.desktop
    
    def run_all_tests(self):
        """Run all test categories"""
        self.logger.log_info("\n" + "="*100)
        self.logger.log_info("STARTING COMPREHENSIVE AGENT TESTING")
        self.logger.log_info("="*100 + "\n")
        
        # Test categories
        self.test_basic_tools()
        self.test_navigation_tools()
        self.test_input_tools()
        self.test_system_tools()
        self.test_reasoning_capabilities()
        self.test_conversation_flow()
        self.test_error_handling()
        
        # Generate report
        report_file = self.logger.generate_report()
        return report_file
    
    def _run_test(self, test_name: str, category: str, test_func, expected_keywords: List[str] = None):
        """Run a single test with timing and scoring"""
        self.logger.log_test_start(test_name, category)
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            # Score the result
            score = self._score_result(result, expected_keywords)
            
            status = "PASS" if score >= 70 else "FAIL"
            
            test_result = TestResult(
                test_name=test_name,
                category=category,
                status=status,
                duration=duration,
                score=score,
                actual=str(result.content if hasattr(result, 'content') else result)[:200]
            )
            
            self.logger.log_test_end(test_result)
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                test_name=test_name,
                category=category,
                status="ERROR",
                duration=duration,
                error_message=str(e),
                score=0.0
            )
            self.logger.log_test_end(test_result)
            return test_result
    
    def _score_result(self, result, expected_keywords: List[str] = None) -> float:
        """Score the test result"""
        score = 0.0
        
        # Check if result exists
        if result:
            score += 30
        
        # Check for errors
        if hasattr(result, 'error') and result.error:
            score -= 20
        
        # Check for content
        if hasattr(result, 'content') and result.content:
            score += 30
            
            # Check for expected keywords
            if expected_keywords:
                content_lower = result.content.lower()
                matches = sum(1 for keyword in expected_keywords if keyword.lower() in content_lower)
                keyword_score = (matches / len(expected_keywords)) * 40
                score += keyword_score
        else:
            score += 40  # No keywords to check, give benefit
        
        return min(score, 100)
    
    # ==================== BASIC TOOLS TESTS ====================
    
    def test_basic_tools(self):
        """Test basic tool functionality"""
        self.logger.log_info("\n--- TESTING BASIC TOOLS ---\n")
        
        # Test Launch Tool
        self._run_test(
            "Launch Tool - Open Notepad",
            "Basic Tools",
            lambda: self.agent.invoke("Open notepad"),
            expected_keywords=["notepad", "opened", "launched"]
        )
        
        time.sleep(1)
        
        # Test Done Tool
        self._run_test(
            "Done Tool - Simple Response",
            "Basic Tools",
            lambda: self.agent.invoke("Say hello to me"),
            expected_keywords=["hello", "hi"]
        )
        
        # Test Wait Tool
        self._run_test(
            "Wait Tool - Delay Execution",
            "Basic Tools",
            lambda: self.agent.invoke("Wait for 2 seconds"),
            expected_keywords=["wait", "seconds"]
        )
    
    # ==================== NAVIGATION TOOLS TESTS ====================
    
    def test_navigation_tools(self):
        """Test navigation and window management tools"""
        self.logger.log_info("\n--- TESTING NAVIGATION TOOLS ---\n")
        
        # Test Switch Tool
        self._run_test(
            "Switch Tool - Switch to Notepad",
            "Navigation",
            lambda: self.agent.invoke("Switch to notepad"),
            expected_keywords=["switch", "notepad"]
        )
        
        time.sleep(1)
        
        # Test Scroll Tool
        self._run_test(
            "Scroll Tool - Scroll Down",
            "Navigation",
            lambda: self.agent.invoke("Scroll down 3 times"),
            expected_keywords=["scroll"]
        )
    
    # ==================== INPUT TOOLS TESTS ====================
    
    def test_input_tools(self):
        """Test input tools (type, click, etc.)"""
        self.logger.log_info("\n--- TESTING INPUT TOOLS ---\n")
        
        # Test Type Tool
        self._run_test(
            "Type Tool - Type Text",
            "Input Tools",
            lambda: self.agent.invoke("Type 'Hello World' in notepad"),
            expected_keywords=["type", "hello world"]
        )
        
        time.sleep(1)
        
        # Test Shortcut Tool
        self._run_test(
            "Shortcut Tool - Select All",
            "Input Tools",
            lambda: self.agent.invoke("Press Ctrl+A to select all"),
            expected_keywords=["ctrl", "select", "all"]
        )
        
        # Test Key Tool
        self._run_test(
            "Key Tool - Press Delete",
            "Input Tools",
            lambda: self.agent.invoke("Press delete key"),
            expected_keywords=["delete", "press"]
        )
        
        # Test Clipboard Tool
        self._run_test(
            "Clipboard Tool - Copy to Clipboard",
            "Input Tools",
            lambda: self.agent.invoke("Copy 'test data' to clipboard"),
            expected_keywords=["copy", "clipboard"]
        )
    
    # ==================== SYSTEM TOOLS TESTS ====================
    
    def test_system_tools(self):
        """Test system-related tools"""
        self.logger.log_info("\n--- TESTING SYSTEM TOOLS ---\n")
        
        # Test System Tool
        self._run_test(
            "System Tool - Get CPU Info",
            "System Tools",
            lambda: self.agent.invoke("Show me CPU usage"),
            expected_keywords=["cpu", "usage", "percent"]
        )
        
        # Test Shell Tool
        self._run_test(
            "Shell Tool - Run PowerShell Command",
            "System Tools",
            lambda: self.agent.invoke("Run powershell command: Get-Date"),
            expected_keywords=["status", "response"]
        )
        
        # Test Human Tool
        self._run_test(
            "Human Tool - Ask Question",
            "System Tools",
            lambda: self.agent.invoke("Ask me what my favorite color is using human tool"),
            expected_keywords=["question", "color"]
        )
    
    # ==================== REASONING TESTS ====================
    
    def test_reasoning_capabilities(self):
        """Test agent's reasoning and planning"""
        self.logger.log_info("\n--- TESTING REASONING CAPABILITIES ---\n")
        
        # Test multi-step reasoning
        self._run_test(
            "Multi-Step Task - Open and Type",
            "Reasoning",
            lambda: self.agent.invoke("Open calculator and type 5+5"),
            expected_keywords=["calculator", "type", "5"]
        )
        
        time.sleep(2)
        
        # Test context understanding
        self._run_test(
            "Context Understanding - Follow-up",
            "Reasoning",
            lambda: self.agent.invoke("Now close it"),
            expected_keywords=["close", "calculator"]
        )
        
        # Test error recovery
        self._run_test(
            "Error Recovery - Invalid Request",
            "Reasoning",
            lambda: self.agent.invoke("Open application that doesn't exist xyz123"),
            expected_keywords=["not", "found", "fail", "error", "unable"]
        )
    
    # ==================== CONVERSATION TESTS ====================
    
    def test_conversation_flow(self):
        """Test conversation and memory capabilities"""
        self.logger.log_info("\n--- TESTING CONVERSATION FLOW ---\n")
        
        # Test greeting
        self._run_test(
            "Greeting Response",
            "Conversation",
            lambda: self.agent.invoke("Hello, how are you?"),
            expected_keywords=["hello", "hi", "help"]
        )
        
        # Test clarification
        self._run_test(
            "Clarification Request",
            "Conversation",
            lambda: self.agent.invoke("What can you do?"),
            expected_keywords=["can", "help", "open", "click", "type"]
        )
        
        # Test conversation clear
        self._run_test(
            "Clear Conversation",
            "Conversation",
            lambda: (self.agent.clear_conversation(), self.agent.invoke("Do you remember our chat?"))[1],
            expected_keywords=["no", "don't", "clear", "new"]
        )
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        self.logger.log_info("\n--- TESTING ERROR HANDLING ---\n")
        
        # Test empty input
        self._run_test(
            "Empty Input Handling",
            "Error Handling",
            lambda: self.agent.invoke(""),
            expected_keywords=[]
        )
        
        # Test invalid coordinates (should be caught)
        self._run_test(
            "Invalid Action Handling",
            "Error Handling",
            lambda: self.agent.invoke("Click at coordinates 999999, 999999"),
            expected_keywords=["error", "invalid", "outside", "fail", "unable"]
        )
        
        # Test complex query
        self._run_test(
            "Complex Query Handling",
            "Error Handling",
            lambda: self.agent.invoke("Open notepad, type 'test', save the file as test.txt in documents folder, then close notepad"),
            expected_keywords=["notepad", "type", "save", "close"]
        )


class ToolRegistryTests:
    """Test individual tools in isolation"""
    
    def __init__(self, test_logger: TestLogger):
        self.logger = test_logger
        self.desktop = Desktop()
        self.registry = Registry([])
    
    def test_all_tools(self):
        """Test each tool individually"""
        self.logger.log_info("\n" + "="*100)
        self.logger.log_info("TESTING INDIVIDUAL TOOLS")
        self.logger.log_info("="*100 + "\n")
        
        # This would test each tool's registry registration
        # For now, we rely on agent-level tests
        pass


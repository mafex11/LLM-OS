"""
Main test runner for Windows-Use Agent
Run this to execute all automated tests and generate reports
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from tests.automated.test_logger import TestLogger
from tests.automated.test_cases import AgentTestCases, ToolRegistryTests

def main():
    """Run all automated tests"""
    print("\n" + "="*100)
    print("WINDOWS-USE AGENT - AUTOMATED TEST SUITE")
    print("="*100 + "\n")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize test logger
    test_logger = TestLogger()
    test_logger.log_info("Initializing test environment...")
    
    # Initialize agent
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
        
        agent = Agent(
            llm=llm,
            browser='chrome',
            use_vision=False,
            enable_conversation=True,
            literal_mode=True,
            max_steps=10,  # Shorter for tests
            enable_tts=False  # Disable TTS for tests
        )
        
        test_logger.log_info("Agent initialized successfully")
        
    except Exception as e:
        test_logger.log_error(f"Failed to initialize agent: {e}")
        return
    
    # Run agent test cases
    test_logger.log_info("Starting agent test cases...")
    agent_tests = AgentTestCases(agent, test_logger)
    
    try:
        report_file = agent_tests.run_all_tests()
        
        print("\n" + "="*100)
        print("TEST SUITE COMPLETED")
        print("="*100)
        print(f"\nDetailed report saved to: {report_file}")
        print(f"Check the 'tests/automated/results/' folder for all test outputs\n")
        
    except Exception as e:
        test_logger.log_error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            agent.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()


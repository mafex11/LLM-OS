from langchain_core.messages import BaseMessage,HumanMessage
from windows_use.agent.views import AgentData
import json
import ast
import re

def read_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()
    
def extract_agent_data(message: BaseMessage) -> AgentData:
    text = message.content
    # Dictionary to store extracted values
    result = {}
    # Extract Memory (disabled)
    # memory_match = re.search(r"<memory>(.*?)<\/memory>", text, re.DOTALL)
    # if memory_match:
    #     result['memory'] = memory_match.group(1).strip()
    # Ensure key exists to avoid attribute errors downstream
    result['memory'] = ""
    # Extract Evaluate
    evaluate_match = re.search(r"<evaluate>(.*?)<\/evaluate>", text, re.DOTALL)
    if evaluate_match:
        result['evaluate'] = evaluate_match.group(1).strip()
    # Extract Plan
    plan_match = re.search(r"<plan>(.*?)<\/plan>", text, re.DOTALL)
    if plan_match:
        result['plan'] = plan_match.group(1).strip()
    # Extract Thought
    thought_match = re.search(r"<thought>(.*?)<\/thought>", text, re.DOTALL)
    if thought_match:
        result['thought'] = thought_match.group(1).strip()
    # Extract Action-Name
    action = {}
    action_name_match = re.search(r"<action_name>(.*?)<\/action_name>", text, re.DOTALL)
    if action_name_match:
        action['name'] = action_name_match.group(1).strip()
    # Extract and convert Action-Input to a dictionary
    action_input_match = re.search(r"<action_input>(.*?)<\/action_input>", text, re.DOTALL)
    if action_input_match:
        action_input_str = action_input_match.group(1).strip()
        try:
            # Convert string to dictionary safely using ast.literal_eval
            action['params'] = ast.literal_eval(action_input_str)
        except (ValueError, SyntaxError):
            try:
                # If there's an issue with conversion, try JSON parsing
                action['params'] = json.loads(action_input_str)
            except (ValueError, SyntaxError):
                # If both fail, log the error and provide a default
                print(f"Warning: Could not parse action_input: {action_input_str}")
                action['params'] = {}
    else:
        # If no action_input found, log the error and provide empty params
        print(f"Warning: No action_input found for action: {action.get('name', 'Unknown')}")
        print(f"Full text: {text}")
        action['params'] = {}
    result['action'] = action
    return  AgentData.model_validate(result)

def image_message(prompt,image)->HumanMessage:
    return HumanMessage(content=[
        {
            "type": "text",
            "text": prompt,
        },
        {
            "type": "image_url", 
            "image_url": {
                "url": image
            }
        },
    ])

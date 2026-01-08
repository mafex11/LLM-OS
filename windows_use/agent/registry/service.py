from windows_use.agent.registry.views import Tool as ToolData, ToolResult
from windows_use.desktop.service import Desktop
from langchain.tools import Tool
from textwrap import dedent

class Registry:
    def __init__(self,tools:list[Tool]):
        self.tools=tools
        # Allow common alias spellings to avoid needless failures
        self.alias_map = {
            'DoneTool': 'Done Tool',
            'doneTool': 'Done Tool',
            'donetool': 'Done Tool',
            'Done': 'Done Tool',
            'done': 'Done Tool',
        }
        self.tools_registry=self.registry()

    def tool_prompt(self, tool_name: str) -> str:
        tool = self.tools_registry.get(tool_name)
        if tool is None:
            return f"Tool '{tool_name}' not found."
        return dedent(f"""
        Tool Name: {tool.name}
        Description: {tool.description}
        Parameters: {tool.params}
        """)

    def registry(self):
        return {tool.name: ToolData(
            name=tool.name,
            description=tool.description,
            params=tool.args,
            function=tool.run
        ) for tool in self.tools}
    
    def get_tools_prompt(self) -> str:
        tools_prompt = [self.tool_prompt(tool.name) for tool in self.tools]
        return '\n\n'.join(tools_prompt)
    
    def execute(self, tool_name: str, desktop: Desktop, **kwargs) -> ToolResult:
        # Normalize known aliases first
        normalized_name = self.alias_map.get(tool_name, tool_name)
        tool = self.tools_registry.get(normalized_name)
        if tool is None:
            return ToolResult(is_success=False, error=f"Tool '{tool_name}' not found.")
        try:
            content = tool.function(tool_input={'desktop':desktop}|kwargs)
            return ToolResult(is_success=True, content=content)
        except Exception as error:
            return ToolResult(is_success=False, error=str(error))
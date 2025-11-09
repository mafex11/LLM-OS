from pydantic import BaseModel,Field
from typing import Literal

class SharedBaseModel(BaseModel):
    class Config:
        extra='allow'

class Done(SharedBaseModel):
    answer:str = Field(...,description="A natural, conversational response to the user query. Respond like a helpful person, not a robot. Use natural language, avoid lists or bullet points unless specifically needed. Include specific details in a flowing, conversational manner.",examples=["There are 6 tabs open in your Chrome browser. I can see your Gmail inbox with over 5,000 emails, a GitHub repository about Windows automation, and a few other development-related pages you're working on."])

class Clipboard(SharedBaseModel):
    mode:Literal['copy','paste'] = Field(...,description="the mode of the clipboard",examples=['Copy'])
    text:str = Field(...,description="the text to copy to clipboard",examples=["hello world"])

class Click(SharedBaseModel):
    loc:tuple[int,int]=Field(...,description="The coordinate within the bounding box of the element to click on.",examples=[(0,0)])
    button:Literal['left','right','middle']=Field(description='The button to click on the element.',default='left',examples=['left'])
    clicks:Literal[0,1,2]=Field(description="The number of times to click on the element. (0 for hover, 1 for single click, 2 for double click)",default=2,examples=[0])

class Shell(SharedBaseModel):
    command:str=Field(...,description="The PowerShell command to execute.",examples=['Get-Process'])

class Resize(SharedBaseModel):
    name:str=Field(...,description="The name of the application window to resize.",examples=['Google Chrome'])
    loc:tuple[int,int]=Field(...,description="The cordinates to move the window to.",examples=[(0,0)])
    size:tuple[int,int]=Field(...,description="The size to resize the window to.",examples=[(100,100)])

class Type(SharedBaseModel):
    loc:tuple[int,int]=Field(...,description="The coordinate within the bounding box of the element to type on.",examples=[(0,0)])
    text:str=Field(...,description="The text to type on the element.",examples=['hello world'])
    clear:Literal['true','false']=Field(description="To clear the text field before typing.",default='false',examples=['true'])
    caret_position:Literal['start','idle','end']=Field(description="The position of the caret.",default='idle',examples=['start','idle','end'])
    press_enter:Literal['true','false']=Field(description="To press enter after typing.",default='false',examples=['true'])

class Launch(SharedBaseModel):
    name:str=Field(...,description="The name of the application to launch.",examples=['Google Chrome'])

class Scroll(SharedBaseModel):
    loc:tuple[int,int]|None=Field(description="The coordinate within the bounding box of the element to scroll on. If None, the screen will be scrolled.",default=None,examples=[(0,0)])
    type:Literal['horizontal','vertical']=Field(description="The type of scroll.",default='vertical',examples=['vertical'])
    direction:Literal['up','down','left','right']=Field(description="The direction of the scroll.",default=['down'],examples=['down'])
    wheel_times:int=Field(description="The number of times to scroll.",default=1,examples=[1,2,5])

class Drag(SharedBaseModel):
    from_loc:tuple[int,int]=Field(...,description="The from coordinates of the drag.",examples=[(0,0)])
    to_loc:tuple[int,int]=Field(...,description="The to coordinates of the drag.",examples=[(100,100)])

class Move(SharedBaseModel):
    to_loc:tuple[int,int]=Field(...,description="The coordinates to move to.",examples=[(100,100)])

class Shortcut(SharedBaseModel):
    shortcut:list[str]=Field(...,description="The shortcut to execute by pressing the keys.",examples=[['ctrl','a'],['alt','f4']])

class Switch(SharedBaseModel):
    name:str=Field(...,description="The name of the application to switch to foreground.",examples=['Google Chrome'])

class Key(SharedBaseModel):
    key:str=Field(...,description="The key to press.",examples=['enter'])

class Wait(SharedBaseModel):
    duration:int=Field(...,description="The duration to wait in seconds.",examples=[2])

class Scrape(SharedBaseModel):
    url:str=Field(...,description="The url of the webpage to scrape.",examples=['https://google.com'])

class Human(SharedBaseModel):
    question:str=Field(...,description="The question to ask the user for clarification or permission.",examples=["The command failed. Would you like me to search for a solution on the web?"])

class System(SharedBaseModel):
    info_type:Literal['all','cpu','memory','disk','processes','summary']=Field(description="The type of system information to retrieve. 'all' for complete analysis, 'summary' for quick overview, or specific categories.",default='all',examples=['all','cpu','memory'])

class Schedule(SharedBaseModel):
    name:str=Field(...,description="The application name to launch from Start menu (e.g., 'calculator', 'chrome').",examples=["calculator","chrome"]) 
    delay_seconds:int|None=Field(default=None,description="How many seconds from now to run. Use this for phrases like 'in 10 seconds'. For repeating tasks, this is the initial delay before first run.")
    run_at:str|None=Field(default=None,description="Absolute local time to run, accepts HH:MM (24h) or ISO-8601 like '2025-11-03T10:00:00'. For phrases like 'at 10 am'. For repeating tasks, this is the start time each day.")
    repeat_interval_seconds:int|None=Field(default=None,description="Interval in seconds for repeating tasks within a day. Examples: 600 for every 10 minutes, 7200 for every 2 hours. Use this for phrases like 'every 10 minutes' or 'every 2 hours'.",examples=[600,7200,3600])
    repeat_end_time:str|None=Field(default=None,description="End time in HH:MM format (24-hour) to stop repeating. For example, '18:30' means stop repeating after 6:30 PM. If not provided, tasks repeat until midnight.",examples=["18:30","22:00"])

class Activity(SharedBaseModel):
    query:str=Field(...,description="The user's question about their activity, productivity, or focus. Examples: 'How focused was I today?', 'Did I do well?', 'What apps did I use most?', 'How much time did I spend on work?'",examples=["How focused was I today?","Did I do well?","What apps did I use the most today?"])
    date:str|None=Field(default=None,description="Specific date to query (YYYY-MM-DD format). If not provided, defaults to today.",examples=["2025-01-15"])

class Timeline(SharedBaseModel):
    query:str=Field(...,description="The user's question about what they were doing at a specific time. Examples: 'What was I doing at 4pm?', 'What did I do between 2pm and 5pm?', 'How did I do today?', 'What was I working on this afternoon?'",examples=["What was I doing at 4pm?","What did I do between 2pm and 5pm?","How did I do today?"])
    date:str|None=Field(default=None,description="Specific date to query (YYYY-MM-DD format). If not provided, defaults to today.",examples=["2025-01-15"])
    start_time:str|None=Field(default=None,description="Start time in HH:MM format (24-hour). Extract from query if user mentions specific times like '4pm', '16:00', '4-6pm', etc.",examples=["16:00","14:00"])
    end_time:str|None=Field(default=None,description="End time in HH:MM format (24-hour). Extract from query if user mentions time ranges like '4-6pm', 'between 2pm and 5pm', etc.",examples=["18:00","17:00"])
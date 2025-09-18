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

class VoiceInput(SharedBaseModel):
    duration:int=Field(...,description="Duration in seconds to listen for voice input.",examples=[5,10,15])
    wake_word:str=Field(...,description="Wake word to activate voice input (e.g., 'hey windows use').",examples=["hey windows use","computer","assistant"])
    mode:Literal['push_to_talk','continuous','wake_word']=Field(...,description="Voice input mode: push_to_talk (press key to talk), continuous (always listening), wake_word (listen for specific word).",examples=['wake_word'])

class VoiceOutput(SharedBaseModel):
    text:str=Field(...,description="Text to convert to speech.",examples=["Hello! I'm ready to help you with Windows automation."])
    voice:Literal['default','male','female']=Field(description="Voice type for speech output.",default='default',examples=['default'])
    rate:int=Field(description="Speech rate (words per minute).",default=200,examples=[150,200,250])

class VoiceMode(SharedBaseModel):
    mode:Literal['on','off','toggle']=Field(...,description="Enable, disable, or toggle voice interaction mode.",examples=['on'])
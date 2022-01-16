from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Room(BaseModel):
    room_name: str
    room_logo_url: str
    members: list[str] = []


class Message(BaseModel):
    author: Optional[str]
    room: Optional[str]
    content: str
    media_url: Optional[str]
    timestamp: Optional[datetime] 

class Chat(BaseModel):
    sender: str
    receiver: str
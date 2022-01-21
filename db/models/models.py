from email import message
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Room(BaseModel):
    room_name: str
    room_logo_url: str
    members: list[str] = []


class Message(BaseModel):
    message: str
    media_url: Optional[str]

class Chat(BaseModel):
    sender: str
    receiver: str
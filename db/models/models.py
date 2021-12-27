from pydantic import BaseModel
from typing import Optional

class Room(BaseModel):
    room_name: str
    room_logo_url: str
    members: list[str] = []


class Message(BaseModel):
    room: str
    content: str
    media_url: Optional[str]

class Chat(BaseModel):
    sender: str
    receiver: str
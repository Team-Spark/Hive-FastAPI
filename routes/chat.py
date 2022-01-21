from datetime import datetime
from fastapi import APIRouter, Depends
from db.models.user import User
from db.models.models import Chat, Message
from db.config.db import db
from auth.oauth import get_current_user, UserInDB
from pydantic import BaseModel
from utils.utils import generate_short_id
from fastapi.responses import JSONResponse
from db.models.models import Message
from typing import Optional


chat = APIRouter(tags=["Chat 💬"],)

class MessageInDB(Message):
    room_short_id: str
    author: str
    short_id: Optional[str]
    timestamp: Optional[datetime] 

class ChatInDB(Chat):
    type: str
    room_short_id: str
    messages: list[MessageInDB] = []

class ChatRes(ChatInDB):
    messages: list[MessageInDB]






@chat.get('/api/v1/chat/{username}', response_model=ChatInDB)
async def get_or_create_chat(username: str, user: UserInDB = Depends(get_current_user)):
    friend = db.users.find_one({"username": username})
    if friend:
        one = db.chats.find_one({"sender": user.username, "receiver": username})
        two = db.chats.find_one({"sender": username, "receiver": user.username})
        if one:
            instance = one
        elif two:
            instance = two
        else:
            data = {
                'sender': user.username,
                'receiver': username,
                'type': 'chat',
                'room_short_id': generate_short_id()
            }
            db.chats.insert_one(data)
            instance = db.chats.find_one({'short_id': data["short_id"]})
        chat_data = ChatInDB(**instance)
        messages_from_db = db.messages.find({"room": chat_data.short_id})
        messages = []
        for datum in messages_from_db:
            messages.append(MessageInDB(**datum))
        chat_data.messages = messages
        return chat_data
    return JSONResponse({'message': "user does not exist"})

@chat.post('/api/v1/chat/message/{room_short_id}')
async def send_message(message: Message, room_short_id: str, user: UserInDB = Depends(get_current_user)):
    message_dict = {
        'author': user.username,
        'room_short_id': room_short_id,
        'timestamp': datetime.now(),
        'short_id': generate_short_id()
    }

    message= MessageInDB(**message.dict(), **message_dict)
    db.messages.insert_one(dict(message))
    return message

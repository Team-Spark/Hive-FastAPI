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
    short_id: Optional[str]

class ChatInDB(Chat):
    short_id: str
    messages: list[Message] = []

class ChatRes(ChatInDB):
    messages: list[Message]




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
                'short_id': generate_short_id()
            }
            db.chats.insert_one(data)
            instance = db.chats.find_one({'short_id': data["short_id"]})
        chat_data = ChatInDB(**instance)
        messages_from_db = db.messages.find({"room": chat_data.short_id})
        messages = []
        for datum in messages_from_db:
            messages.append(Message(**datum))
        chat_data.messages = messages
        return chat_data
    return JSONResponse({'message': "user does not exist"})

@chat.post('/api/v1/chat/message/{short_id}')
async def send_message(message: Message, short_id: str, user: UserInDB = Depends(get_current_user)):
    message.author = user.username
    message.room = short_id
    message.timestamp = datetime.now()
    db.messages.insert_one(dict(message))
    return message

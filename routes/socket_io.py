import socketio
from routes.chat import MessageInDB
from utils import config
from typing import Any
from auth.oauth import get_sio_user
import json
from datetime import datetime, timezone
from utils.utils import generate_short_id
from db.models.models import Message
from db.config.db import db



mgr = socketio.AsyncRedisManager(config.REDIS_URL)

sio: Any = socketio.AsyncServer(async_mode="asgi", client_manager=mgr, cors_allowed_origins="*")


@sio.on("connect")
async def connect(sid, env, auth):
    if auth:
        user = await get_sio_user(auth["token"])
        room_short_id = auth['room_short_id']
        if user:
            print("SocketIO connect")
            sio.enter_room(sid, str(room_short_id))
            await sio.emit("connect", f"User {user.username} connected as {sid}")
        else:
            raise ConnectionRefusedError("authentication failed")
    else:
        # raise ConnectionRefusedError("no auth token")
        await sio.emit("connect", f"User test connected as {sid}")

@sio.on('message')
async def print_message(sid, data):
    print("Socket ID", sid)
    data = json.loads(data)
    room = data['room_short_id']
    message_data = {
                        "author": data["username"],
                        "message": data["message"],
                        "room_short_id": data['room_short_id'],
                        "short_id": generate_short_id(),
                        "timestamp": datetime.now()
                    }
                    
    message_serialized = MessageInDB(**message_data)
    db.messages.insert_one(dict(message_serialized))
    message_from_db = (db.messages.find_one({"short_id": message_data["short_id"]}))
    message = dict(Message(**message_from_db))
    await sio.emit("new_message", message, room=room)


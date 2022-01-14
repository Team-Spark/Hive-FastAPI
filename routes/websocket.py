
from typing import Optional, List
from bson import ObjectId

from fastapi import APIRouter
from db.models.user import User
from auth.oauth import get_current_websocket_user
from fastapi import Cookie, Depends, FastAPI, Query, WebSocket, status
from fastapi.responses import HTMLResponse
from db.config.db import db
from datetime import datetime
from db.schemas.room import serialize_room

from db.schemas.user import serialize_dict
from utils.utils import generate_short_id

socket = APIRouter()



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)
manager = ConnectionManager()


@socket.websocket("/ws/room/{short_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    short_id: str,
    user: User = Depends(get_current_websocket_user),
):  
    room = serialize_dict(db.rooms.find_one({"short_id": short_id}))
    if room is None:
        websocket.close(code=status.HTTP_404_NOT_FOUND)
    await manager.connect(websocket)
    while True:
        data = await websocket.receive_json()
        if "command" in data:
            if data["command"] == "new_message":
                message_data = {
                    "author": user.username,
                    "content": data["content"],
                    "room": ObjectId(room['id']),
                    "media_url": (data["media_url"] if "media_url" in data else None),
                    "timestamp": datetime.now(),
                    "short_id": generate_short_id()
                }
                db.messages.insert_one(message_data)
                message = serialize_room( db.messages.find_one({"short_id": message_data["short_id"]}))
                print(message)
                await manager.broadcast(
                    {"message": message}
                )
        
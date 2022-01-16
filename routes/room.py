from fastapi import APIRouter
from pydantic.main import BaseModel
from starlette import status
from starlette.responses import JSONResponse
from fastapi.param_functions import Depends
from db.models.models import Room
from db.models.user import User
from auth.oauth import get_current_user
from db.config.db import db
from datetime import datetime
from utils.utils import generate_short_id

room = APIRouter(tags=["Room 🧑‍🤝‍🧑💬"])
class RoomCreate(Room):
    creator: str
    short_id: str
class RoomResponse(BaseModel):
    message: str
    room: RoomCreate
    failed_users: list[str]

@room.post('/api/v1/room/create', response_model=RoomResponse)
async def create_room(room: Room, current_user: User = Depends(get_current_user)):
    wrong_users = []
    for member in room.members:
        if db.users.find_one({'username': member}) == None:
            wrong_users.append(member)
            room.members.remove(member)
    if db.rooms.find_one({"room_name": room.room_name}):
        return JSONResponse({"message": "room name already exists"}, status_code=status.HTTP_208_ALREADY_REPORTED)
    data = {
        'creator': current_user.username,
        **room.dict(),
        'short_id': str(generate_short_id())
    }
    db.rooms.insert_one(data)
    return {"message": "room created", "room": data, "failed_users": wrong_users}

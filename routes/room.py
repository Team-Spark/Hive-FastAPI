from fastapi import APIRouter
from pydantic.main import BaseModel
from starlette import status
from starlette.responses import JSONResponse
from fastapi.param_functions import Depends
from db.models.models import Room
from db.models.user import User
from auth.oauth import UserInDB, get_current_user
from db.config.db import db
from datetime import datetime
from routes.chat import MessageInDB
from routes.user import ResponseMessage
from utils.utils import generate_short_id, get_new_room_uidb64, decode_room_uidb64
from db.models.models import Message

room = APIRouter(tags=["Room 👥💬"])


class RoomInDB(Room):
    creator: str
    type: str
    room_short_id: str
    room_uidb64: str
    messages: list[MessageInDB] = []

class RoomResponse(BaseModel):
    message: str
    room: RoomInDB
    failed_users: dict

@room.post('/api/v1/rooms', response_model=RoomResponse)
async def create_room(room: Room, current_user: User = Depends(get_current_user)):
    failed = {}
    if db.rooms.find_one({"room_name": room.room_name}):
        return JSONResponse({"message": "room name already exists"}, status_code=status.HTTP_208_ALREADY_REPORTED)
    for member in room.members:
        if db.users.find_one({'username': member}) == None:
            failed[member]= "user does not exist"
            room.members.remove(member)
        if member == current_user.username:
            failed[member] = "user has already been added by default"
            room.members.remove(member)
    room.members.append(current_user.username)
   
    data = {
        'creator': current_user.username,
        **room.dict(),
        "type": 'room', 
        'room_short_id': str(generate_short_id()),
    }
    data['room_uidb64'] = get_new_room_uidb64(data["room_short_id"])
    db.rooms.insert_one(data)
    dbroom = db.rooms.find_one({"room_short_id": data["room_short_id"]})
    return {"message": "room created", "room": RoomInDB(**dbroom), "failed_users": failed}


@room.post('/api/v1/rooms/join/{uidb64}', response_model=ResponseMessage)
async def join_room_with_link(uidb64: str, user: UserInDB = Depends(get_current_user)):
    try:
        room_short_id = decode_room_uidb64(uidb64)
    except Exception as e:
        return JSONResponse({"message": "Invalid Link"}, status_code=status.HTTP_400_BAD_REQUEST)
    room_in_db = db.rooms.find_one({'room_short_id': room_short_id})
    if room_in_db:
        room = RoomInDB(**(room_in_db))
    else:
        return JSONResponse({"message": "Invalid Link"}, status_code=status.HTTP_400_BAD_REQUEST)
    if room.room_uidb64 != uidb64:
        return JSONResponse({"message": "Link has been reset"}, status_code=status.HTTP_400_BAD_REQUEST)
    if user.username in room.members:
        return JSONResponse({"message": "You are already in this room"}, status_code=status.HTTP_200_OK)
    room.members.append(user.username)
    db.rooms.find_one_and_update({'room_short_id': room_short_id}, {"$set": {'members': room.members}})
    return {"message": "You have succesfully been added to this room"}

@room.get('/api/v1/room/{room_short_id}', response_model=RoomInDB)
async def get_room(room_short_id: str, user: UserInDB = Depends(get_current_user)):
    instance = db.rooms.find_one({"room_short_id": room_short_id})
    if instance:
        chat_data = RoomInDB(**instance)
        messages_from_db = db.messages.find({"room_short_id": chat_data.room_short_id})
        messages = []
        for datum in messages_from_db:
            messages.append(MessageInDB(**datum))
        chat_data.messages = messages
        return chat_data
    return JSONResponse({'message': "room does not exist"}, status_code=status.HTTP_404_NOT_FOUND)

@room.put('/api/v1/room/{room_short_id}/reset-link', response_model=ResponseMessage)
async def reset_room_link(room_short_id: str, user: UserInDB = Depends(get_current_user)):
    instance = db.rooms.find_one({"room_short_id": room_short_id})
    if instance:
        room_data = RoomInDB(**instance)
        if room_data.creator != user.username:
            return JSONResponse({"message": "Only the group creator can reset the link"}, status_code=status.HTTP_400_BAD_REQUEST)
        room_data.room_uidb64 = get_new_room_uidb64(room_data.room_short_id)
        db.rooms.find_one_and_update({"room_short_id": room_data.room_short_id}, {"$set": {"room_uidb64": room_data.room_uidb64}})
        return {"message": f'{room_data.room_uidb64 }'}
    return {"message": "room doesn't exist"}
   


    



from fastapi import APIRouter
from auth.oauth import UserInDB, get_current_user
from fastapi import Depends
from db.config.db import db
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel
from db.models.user import User
from typing import List, Optional
from pymongo.errors import DuplicateKeyError
from auth.oauth import verify_password, get_password_hash
from operator import itemgetter
from routes.chat import ChatInDB, MessageInDB
from db.models.models import Room



user = APIRouter(tags=["User 👤"],)


class RoomInDB(Room):
    creator: str
    type: str
    room_short_id: str
    room_uidb64: str
    messages: list[MessageInDB] = []

class Friends(BaseModel):
    users: list[str]

class AddFriends(BaseModel):
    message: str
    successful: list[str]
    failed: dict

class UserUpdate(BaseModel):
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    image_url: Optional[str]
    about: Optional[str]

class UpdateRes(BaseModel):
    message: str
    user: UserUpdate


class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class ResponseMessage(BaseModel):
    message: str



@user.post('/api/v1/user/friends', response_model=AddFriends)
async def add_friends(friends: Friends, user: UserInDB = Depends(get_current_user)):
    current_friends = user.friends
    new_friends =  friends.users
    successful = []
    failed = {}
    for username in new_friends:
        if username == user.username:
            failed[username] = "Can't add yourself boss" 
            continue
        if username in current_friends:
            failed[username] = "Already in friend list"
            continue
        
        friend = db.users.find_one({'username': username})
        if friend:
            current_friends.append(username)
            db.users.find_one_and_update({'username': user.username}, {'$set': {"friends": current_friends}})
            successful.append(username)
            continue
        failed[username] = "no such user"
    return JSONResponse({'message': 'Done', "successful": successful, 'failed': failed}, status_code=status.HTTP_200_OK)



@user.get('/api/v1/user/friends', response_model=List[User])
async def get_friends(user: UserInDB = Depends(get_current_user)):
    current_friends = user.friends
    response = []
    for username in current_friends:
        user =  db.users.find_one({'username': username})
        response.append(User(**user))
    return response



@user.put('/api/v1/user/update-profile', response_model=UpdateRes)
async def update_profile(update: UserUpdate, user: UserInDB = Depends(get_current_user)):
    data = dict(update)
    if data['username'] == user.username:
        del data['username']
    cleaned_data = data.copy()
    for datum in data:
        if data[datum] == None :
            del cleaned_data[datum]
    if 'username' in cleaned_data:
        existing_user = db.users.find_one({'username': cleaned_data['username']})
        if existing_user:
            return JSONResponse({'message': "username already exists"}, status_code=status.HTTP_208_ALREADY_REPORTED)
    try:
        updated_user = db.users.find_one_and_update({"username": user.username}, {'$set': cleaned_data})
    except DuplicateKeyError:
        return JSONResponse({'message': "username already exists"}, status_code=status.HTTP_208_ALREADY_REPORTED)
    return {"message": "User update successful", 'user': UserUpdate(**updated_user)}


@user.put('/api/v1/user/change-password', response_model=ResponseMessage)
async def change_password(passwords: ChangePassword, user: UserInDB = Depends(get_current_user)):
    password_status = verify_password(passwords.current_password, user.hashed_password)
    if password_status:
        db.users.find_one_and_update({'username': user.username}, {'$set': {'hashed_password': get_password_hash(passwords.new_password)}})
        return {'message': 'password change successful'}
    return JSONResponse({'message': 'incorrect current password'}, status_code=status.HTTP_401_UNAUTHORIZED)



def get_last_message(room_short_id: str):
    message = db.messages.find_one({"room_short_id": room_short_id}).sort({"timestamp":-1})
    return MessageInDB(**message)

    

@user.get('/api/v1/user/get-rooms-and-chats')
async def get_rooms_and_chats(user: UserInDB = Depends(get_current_user)):
    rooms_in_db = db.rooms.find({"members": user.username})
    chats_in_db = db.chats.find( 
                {'$or': [
                    {'receiver': user.username}, 
                    {"sender": user.username}
                    ]
                })

    rooms = [RoomInDB(**room).dict() for room in rooms_in_db]
    chats = [ChatInDB(**chat).dict() for chat in chats_in_db]

    for chat in chats:
        chat_messages_in_db = db.messages.find({"room_short_id": chat['room_short_id']}) 
        messages = [MessageInDB(**message).dict() for message in chat_messages_in_db]
        if len(messages) == 0:
            chats.remove(chat)
        elif chat["receiver"] == user.username:
            friend_in_db = db.users.find_one({'username': chat["sender"]})
            friend = User(**friend_in_db).dict()
            chat['friend'] = friend
        elif chat["sender"] == user.username:
            friend_in_db = db.users.find_one({'username': chat["receiver"]})
            friend = User(**friend_in_db).dict()
            chat['friend'] = friend

    user_rooms = rooms + chats
    for item in user_rooms:
        last_message = get_last_message(item['room_short_id'])
        item["last_message"] = last_message
        item["last_timestamp"] = last_message.timestamp


    sorted_list_by_last_message = sorted(user_rooms, key=itemgetter("last_timestamp"), reverse=True)
    return sorted_list_by_last_message
    

        

    

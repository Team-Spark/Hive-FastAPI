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


user = APIRouter(tags=["User 👤"],)

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
    

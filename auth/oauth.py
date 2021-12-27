from datetime import datetime, timedelta
from re import I
from typing import Optional
import os
from fastapi import Depends, FastAPI, HTTPException, status, WebSocket, Query
from bson import ObjectId
from db.config.db import db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from db.schemas.user import auth_serializer, serialize_dict, serialize_list
from dotenv import load_dotenv
load_dotenv()

from db.config.db import db as hive_db

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = str(os.getenv('SECRET_KEY'))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauthroute = FastAPI()


# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "full_name": "John Doe",
#         "email": "johndoe@example.com",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
#         "disabled": False,
#     }
# }


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str
    is_verified: bool


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")




def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    user = db.users.find_one({'username': username})
    if user:
        user_dict = auth_serializer(user)
        return UserInDB(**user_dict)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(hive_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_websocket_user(websocket: WebSocket, token: Optional[str] = Query(None)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(hive_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return user


@oauthroute.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@oauthroute.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]




@oauthroute.get('/users')
async def find_all_users():
    return serialize_list(db.users.find())

@oauthroute.get('/user/{id}')
async def get_single_user(id: str):
    return serialize_dict(db.users.find_one({"_id": ObjectId(id)}))


@oauthroute.put('/user/{id}')
async def update_user(id: str, use: User):
    db.users.find_one_and_update({"_id":ObjectId(id)}, {"$set": dict(use)})
    return serialize_dict(db.users.find_one({"_id": ObjectId}))

@oauthroute.delete('/user/{id}')
async def delete_user(id: str):
    return serialize_dict(db.users.find_one_and_delete({"_id": ObjectId(id)}))





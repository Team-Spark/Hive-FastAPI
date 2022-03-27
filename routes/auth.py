from fastapi import APIRouter, Request
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from db.scripts.dbservice import *
from pymongo import message
from auth.oauth import *
from bson import ObjectId, objectid
from db.models.user import User
from db.config.db import db
from fastapi_mail.errors import ConnectionErrors
from db.schemas.user import serialize_dict, serialize_list
from mail.mail_service import send_activation_email, send_reset_password_email
from starlette.responses import JSONResponse
from utils.config import BACKEND_URL
from pymongo.errors import DuplicateKeyError
from typing import Any

user = APIRouter(
    tags=["Auth 🔐"],
)


class UserReg(User):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.username = self.username.lower()


class RegRes(BaseModel):
    message: str
    user: User


class LoginRes(BaseModel):
    message: str
    user: User
    access_token: str


class ResetPassword(BaseModel):
    password: str


@user.post("/api/v1/auth/login", response_model=Token)
async def login(data: UserLogin):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        return JSONResponse(
            {"message": "Incorrect username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_verified == False:
        return JSONResponse(
            {"message": "email not verified"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"message": "Login Successful", "user": user, "access_token": access_token}


@user.post("/token", response_model=Token)
async def login_for_access_token(data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        return JSONResponse(
            {"message": "Incorrect username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_verified == False:
        return JSONResponse(
            {"message": "email not verified"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires": f"{ACCESS_TOKEN_EXPIRE_MINUTES}",
    }


@user.post(
    "/api/v1/auth/register", status_code=status.HTTP_201_CREATED, response_model=RegRes
)
async def create_user(reg: UserReg):
    if db.users.find_one({"username": reg.username}):
        return JSONResponse(
            {"message": "username already exists"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    elif db.users.find_one({"email": reg.email}):
        return JSONResponse(
            {"message": "email already exists"}, status_code=status.HTTP_400_BAD_REQUEST
        )
    data = {
        "username": reg.username,
        "first_name": reg.first_name,
        "last_name": reg.last_name,
        "email": reg.email,
        "hashed_password": get_password_hash(reg.password),
        "image_url": reg.image_url,
        "is_verified": False,
        "friends": [],
        "created_at": datetime.now(),
    }

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": reg.email}, expires_delta=access_token_expires
    )
    try:
        db.users.insert_one(data)
    except DuplicateKeyError:
        return JSONResponse(
            {"message": "username or email already exists"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        await send_activation_email(
            reg.email,
            {"url": BACKEND_URL, "username": reg.username, "token": access_token},
        )

    except ConnectionErrors:
        return JSONResponse(
            {"message": "failed to send email due to smtp connection errors"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return {
        "message": "Registration succesful, check email",
        "user": serialize_dict(db.users.find_one({"username": reg.username})),
    }


@user.get("/api/v1/auth/verify-email/{token}", status_code=status.HTTP_200_OK)
async def verify_email(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return JSONResponse(
                {"message": "verification failed, token expired"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        verification = {"is_verified": True}
        if db.users.find_one({"email": email}):
            db.users.find_one_and_update({"email": email}, {"$set": verification})
            return {"message": "verification succesful"}
        else:
            return {"message": f"email: {email} doesn't exist in our database"}
    except JWTError:
        return JSONResponse(
            {"message": "verification failed, token expired"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@user.post(
    "/api/v1/auth/resend-verification-email/{email}", status_code=status.HTTP_200_OK
)
async def resend_verification_email(email: str):
    user = db.users.find_one({"email": email})
    if user:

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        user = serialize_dict(db.users.find_one({"email": email}))
        if user["is_verified"]:
            return JSONResponse(
                {"message": "user already verified"},
                status_code=status.HTTP_208_ALREADY_REPORTED,
            )
        try:
            await send_activation_email(
                email,
                {
                    "url": BACKEND_URL,
                    "username": user["username"],
                    "token": access_token,
                },
            )

        except ConnectionErrors as e:
            return JSONResponse(
                {"message": f"failed to send email due to smtp connection errors: {e}"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return {"message": "verification email sent"}
    else:
        return JSONResponse(
            {"message": "email doesn't exist"}, status_code=status.HTTP_400_BAD_REQUEST
        )


@user.post("/api/v1/auth/forgot-password/{email}", status_code=status.HTTP_200_OK)
async def forgot_password(email: str):
    user = db.users.find_one({"email": email})
    if user:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        try:
            await send_reset_password_email(
                email,
                {
                    "url": BACKEND_URL,
                    "username": user["username"],
                    "token": access_token,
                },
            )

        except ConnectionErrors:
            return JSONResponse(
                {"message": "failed to send email due to smtp connection errors"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return {"message": "reset password email sent"}
    else:
        return JSONResponse(
            {"message": f"user with email {email} doesn't exist"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@user.put("/api/v1/auth/reset-password/{token}", status_code=status.HTTP_200_OK)
async def reset_password(token: str, reset: ResetPassword):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return JSONResponse(
                {"message": "reset password failed, token expired"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data = {"hashed_password": get_password_hash(reset.password)}
        db.users.find_one_and_update({"email": email}, {"$set": data})
    except JWTError:
        return JSONResponse(
            {"message": "reset password failed, token expired"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return {"message": "password reset succesful"}

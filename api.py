from fastapi import FastAPI, Request, Response
from routes.auth import user
from routes.room import room
from routes.user import user as user_actions
from routes.websocket import socket
from routes.chat import chat
from core.config import Settings
from functools import lru_cache
from db.models.user import User

import socketio
from routes.socket_io import sio

# from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

app = FastAPI(
    title="Hive",
    description="Hive Apis",
    version="0.0.1",
)

app.include_router(user)
app.include_router(room)
app.include_router(socket)
app.include_router(user_actions)
app.include_router(chat)
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup():
    User.init()

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


def create_app() -> CORSMiddleware:
    """Create app wrapper to overcome middleware issues."""
    fastapi_app = FastAPI(
        title="Hive",
        description="Hive Apis",
        version="0.0.1",
    )
    fastapi_app.include_router(user)
    fastapi_app.include_router(room)
    fastapi_app.include_router(socket)
    fastapi_app.include_router(user_actions)
    fastapi_app.include_router(chat)

    return CORSMiddleware(
        fastapi_app,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app = create_app()


socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)  # Here we mount socket app to main fastapi app


@app.on_event("startup")
async def startup():
    User.init()


# or 'foo.com', etc.

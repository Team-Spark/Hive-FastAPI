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

# middleware = [
#     Middleware(
#         CORSMiddleware,
#         allow_origins=['*'],
#         allow_credentials=True,
#         allow_methods=['*'],
#         allow_headers=['*']
#     )
# ]

app = FastAPI(
    title="Hive",
    description="Hive Apis",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


origins = ["*"]


app.include_router(user)
app.include_router(room)
app.include_router(socket)
app.include_router(user_actions)
app.include_router(chat)


socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)  # Here we mount socket app to main fastapi app


@app.on_event("startup")
async def startup():
    User.init()


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

ALLOWED_ORIGINS = "*"  # or 'foo.com', etc.

# handle CORS preflight requests
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str) -> Response:
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGINS
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return response


# set CORS headers
@app.middleware("http")
async def add_CORS_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGINS
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return response

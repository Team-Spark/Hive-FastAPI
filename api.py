from fastapi import FastAPI
from routes.user import user
from routes.room import room
from routes.websocket import socket
from core.config import Settings
from functools import lru_cache
from websocket_helper import na

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
    },)
app.include_router(user)
app.include_router(room)
app.include_router(socket)
app.include_router(na)

# @lru_cache()
# def get_settings():
#     return Settings()
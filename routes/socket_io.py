import os
import socketio
from utils import config
from typing import Any



mgr = socketio.AsyncRedisManager(config.REDIS_URL)

sio: Any = socketio.AsyncServer(async_mode="asgi", client_manager=mgr, cors_allowed_origins="*")



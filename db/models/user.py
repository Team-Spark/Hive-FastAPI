from pydantic import BaseModel, EmailStr
from typing import Optional
from db.config.db import db


class User(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    image_url: str

    @staticmethod
    def init():
        db.users.create_index([("username", 1)], unique=True)
        db.users.create_index([("email", 1)], unique=True)

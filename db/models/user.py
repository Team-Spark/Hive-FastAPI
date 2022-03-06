from pydantic import BaseModel, EmailStr
from typing import Optional
from db.config.db import db
from typing import Any


class User(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    image_url: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.email = self.email.lower()
        self.username = self.username.lower()
    @staticmethod
    def init():
        db.users.create_index([("username", 1)], unique=True)
        db.users.create_index([("email", 1)], unique=True)

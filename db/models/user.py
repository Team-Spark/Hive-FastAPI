from pydantic import BaseModel, EmailStr
from typing import Optional


class User(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    image_url: str

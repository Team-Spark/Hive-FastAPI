from fastapi import APIRouter
from typing import List
from db.models.user import User
from db.config.db import db


people = APIRouter(tags=["People  👥 "])


@people.get("/api/v1/people", response_model=List[User])
async def find_people(search: str = None):
    if search == None:
        people = db.users.find()
    elif search:
        search = search.rstrip()
        if search == "":
            people = db.users.find()
        else:
            people = db.users.find(
                {
                    "$or": [
                        {"username": {"$regex": f"^{search}", "$options": "i"}},
                        {"email": {"$regex": f"^{search}", "$options": "i"}},
                    ]
                }
            )
    response = [User(**user) for user in people]

    return response

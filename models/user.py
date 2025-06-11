from pydantic import BaseModel
from typing import List
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    CASE_MANAGER = "case_manager"
    ANALYST = "analyst"
    VIEWER = "viewer"

class User(BaseModel):
    username: str
    email: str
    roles: List[UserRole]
    is_active: bool = True

class UserInDB(User):
    hashed_password: str
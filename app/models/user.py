# app/models/user.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum


class Gender(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"
    prefer_not_to_say = "Prefer not to say"


class Choice(str, Enum):
    yes = "Yes"
    no = "No"
    maybe = "Maybe"


class Preferences(BaseModel):
    privacy_policy: Choice
    data_sharing: Choice
    memory_of_searches: Choice
    explanation_of_answers: Choice
    stored_health_data: Choice


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    birthdate: Optional[str] = None  
    gender: Optional[Gender] = None
    medications: List[str] = []
    illness: List[str]=[]
    allergies:List[str]=[]
    nicknames: Optional[dict] = {}
    preferences: Optional[Preferences] = None


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    user_id: str
    hashed_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password:str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    birthdate: Optional[str] = None  # Store as ISO string or convert later
    gender: Optional[str] = None
    medications: Optional[List[str]] = None
    illness: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    nicknames: Optional[dict[str, str]] = None
    preferences: Optional[Preferences] = None

    

class UserOut(BaseModel):
    email: EmailStr
    user_id: Optional[str]  
    first_name: Optional[str]
    last_name: Optional[str]
    preferred_name: Optional[str]
    birthdate: Optional[str]
    gender: Optional[str]
    medications: Optional[List[str]]
    illness: Optional[List[str]]
    allergies: Optional[List[str]]
    nicknames: Optional[dict[str, str]]
    preferences: Optional[Preferences] = None



class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newStrongPass456"
            }
        }

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
    birthdate: Optional[str] = None  # Format MM/DD/YYYY (you can parse later)
    gender: Optional[Gender] = None
    medications: List[str] = []
    illness: List[str]=[]
    allergies:List[str]=[]
    nicknames: Optional[dict] = {}
    preferences: Optional[Preferences] = None


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password:str
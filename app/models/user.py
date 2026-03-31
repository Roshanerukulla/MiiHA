import re
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, field_validator


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
    birthdate: Optional[str] = None  # Format MM/DD/YYYY
    gender: Optional[Gender] = None
    medications: List[str] = []
    nicknames: Optional[Dict[str, str]] = {}  # typed: both keys and values must be strings
    preferences: Optional[Preferences] = None

    @field_validator("birthdate")
    @classmethod
    def validate_birthdate(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", v):
            raise ValueError("Birthdate must be in MM/DD/YYYY format")
        month, day, year = int(v[:2]), int(v[3:5]), int(v[6:])
        if not (1 <= month <= 12):
            raise ValueError("Invalid month in birthdate")
        if not (1 <= day <= 31):
            raise ValueError("Invalid day in birthdate")
        if not (1900 <= year <= 2100):
            raise ValueError("Invalid year in birthdate")
        return v


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Language = Literal["en", "te", "hi", "ta", "kn", "ml", "mr", "bn"]
Level = Literal["beginner", "intermediate", "advanced"]
ScriptPref = Literal["auto", "roman", "native"]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=100)
    preferred_language: Language = "en"


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class ProfileOut(BaseModel):
    display_name: str
    preferred_language: Language
    skill_level: Level
    preferred_script: ScriptPref = "auto"


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    preferred_language: Language | None = None
    skill_level: Level | None = None
    preferred_script: ScriptPref | None = None


class UserOut(BaseModel):
    id: int
    email: str
    profile: ProfileOut


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

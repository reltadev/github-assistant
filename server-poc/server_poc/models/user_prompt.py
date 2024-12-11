from sqlmodel import Field, SQLModel
from sqlalchemy import MetaData
from datetime import datetime
from enum import Enum

class PromptType(Enum):
    DATA_ONLY = 1
    FULL_TEXT = 2

class UserPrompt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    metadata = MetaData()
    prompt: str
    owner: str
    repo: str
    prompt_type: PromptType
    time: datetime | None = None

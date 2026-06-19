from typing import Optional, List
from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    description: Optional[str] = None
    color: Optional[str] = "white"
    is_archived: Optional[bool] = False
    is_pinned: Optional[bool] = False


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


class NoteResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    color: str
    is_archived: bool
    is_pinned: bool
    user_id: int


class ExportRequest(BaseModel):
    user_id: int
    filenames: List[str]

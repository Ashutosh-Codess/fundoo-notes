from pydantic import BaseModel


class LabelCreate(BaseModel):
    name: str


class LabelResponse(BaseModel):
    id: int
    name: str
    user_id: int

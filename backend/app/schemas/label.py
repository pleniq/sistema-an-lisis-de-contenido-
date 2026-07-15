from pydantic import BaseModel


class LabelOut(BaseModel):
    id: str
    name: str


class LabelCreate(BaseModel):
    name: str

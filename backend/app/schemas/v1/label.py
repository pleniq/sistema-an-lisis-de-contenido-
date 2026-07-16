from pydantic import BaseModel


class LabelOut(BaseModel):
    id: str
    name: str
    count: int = 0  # cuántos reels usan esta etiqueta


class LabelCreate(BaseModel):
    name: str


class LabelRename(BaseModel):
    name: str


class LabelRenameResult(BaseModel):
    id: str
    name: str
    merged: bool  # True si se fusionó con una etiqueta existente (dedupe)

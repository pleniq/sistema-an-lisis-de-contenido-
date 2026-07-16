from pydantic import BaseModel


class ExportRequest(BaseModel):
    reel_ids: list[str]


class ExportResponse(BaseModel):
    format: str
    reels: int
    text: str

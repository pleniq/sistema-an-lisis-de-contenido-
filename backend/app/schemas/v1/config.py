from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MetaConfigIn(BaseModel):
    access_token: str
    ig_user_id: Optional[str] = None
    account_name: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None


class MetaConfigStatus(BaseModel):
    connected: bool
    token_status: str  # ok | expired | missing
    ig_user_id: Optional[str] = None
    account_name: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    days_left: Optional[int] = None
    long_lived: bool = False
    last_error: Optional[str] = None

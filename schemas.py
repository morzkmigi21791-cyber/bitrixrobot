from pydantic import BaseModel
from typing import Optional

class ContactCreateDTO(BaseModel):
    last_name: str
    first_name: str
    second_name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""

class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    application_token: Optional[str] = None
    domain: str
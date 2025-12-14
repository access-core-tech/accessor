from pydantic import BaseModel
from uuid import UUID


class UserInfo(BaseModel):
    user_uuid: UUID
    name: str
    is_email_verified: bool = False
    login_email: str
    first_name: str
    second_name: str
    middle_name: str | None = None

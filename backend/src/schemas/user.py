from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_admin: bool
    is_active: bool
    balance: float

    class Config:
        from_attributes = True
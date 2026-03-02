from pydantic import BaseModel, EmailStr


class MeOut(BaseModel):
    public_id: str
    address: str
    email: EmailStr
    balance_usdt: str
    status: str
    role: str
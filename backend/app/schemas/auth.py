from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    profile_picture: str | None = None

    model_config = {
        "from_attributes": True
    }
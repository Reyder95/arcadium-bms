from pydantic import BaseModel

class TierOut(BaseModel):
    name: str
    floor: float
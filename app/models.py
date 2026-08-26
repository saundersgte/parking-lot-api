from pydantic import BaseModel

class Spot(BaseModel):
    spot_id: str
    status: str
    
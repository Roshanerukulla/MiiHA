from pydantic import BaseModel
#rey

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in:int 





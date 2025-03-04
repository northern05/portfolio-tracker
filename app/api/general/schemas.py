from pydantic import BaseModel


class ConnectTwitter(BaseModel):
    """
    Base schema of connect twitter
    """
    wallet_address: str
    twitter_id: str

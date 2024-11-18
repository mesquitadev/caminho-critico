"""Schema health"""

from pydantic import BaseModel


OK = "OK"


class HealthCheck(BaseModel):
    """Classe Health"""

    status: str = OK

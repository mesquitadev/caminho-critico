from pydantic import BaseModel


class JobStatusRequest(BaseModel):
    jobname: str
    keyBB: str
    limit: int
    orderDateFrom: str
    orderDateTo: str
    server: str

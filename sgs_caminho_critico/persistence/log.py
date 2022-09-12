from fastapi_sqlalchemy import db
from db import Logs


async def insert_log(log):
    tuple_db = Logs(**log)
    db.session.add(tuple_db)
    db.session.commit()

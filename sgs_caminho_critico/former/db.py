from sqlalchemy.ext.declarative import declarative_base
import os

from sqlalchemy import (
    Column,
    INTEGER,
    VARCHAR,
    JSON,
    TIMESTAMP,
    SMALLINT
)
from sqlalchemy.dialects.postgresql import INET

schema = os.getenv('AGILIZA_DB_SCHEMA')

Base = declarative_base()
Base.metadata.schema = schema


class Logs(Base):
    __tablename__ = "logs"
    id = Column(INTEGER(), primary_key=True, index=True)
    ip = Column('ip', INET())
    endpoint = Column('endpoint', VARCHAR(length=80), nullable=False)
    method = Column('method', VARCHAR(length=7), nullable=False)
    arguments = Column('arguments', JSON())
    requester = Column('requester', VARCHAR(length=10))
    return_code = Column('return_code', SMALLINT())
    response_data = Column('response_data', JSON())
    begin_timestamp = Column('begin_timestamp', TIMESTAMP(), nullable=False)
    end_timestamp = Column('end_timestamp', TIMESTAMP())


class Tokens(Base):
    __tablename__ = "tokens"
    id = Column(INTEGER(), primary_key=True, nullable=False)
    token = Column(VARCHAR(length=128), nullable=False)
    owner = Column(VARCHAR(length=20), nullable=False)
    reason = Column(VARCHAR(length=200), nullable=False)
    timestamp = Column(TIMESTAMP(), nullable=False)

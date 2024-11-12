import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
database = os.getenv('DB_NAME')
port = os.getenv('DB_PORT')
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

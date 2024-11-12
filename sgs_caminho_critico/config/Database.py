from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sgs_caminho_critico.config import settings

engine = create_engine(settings.pgre_dsn)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

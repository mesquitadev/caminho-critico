import os
from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()

        # Setup Database
        self.sqlite_dsn = 'sqlite:///:memory:'
        self.pgre_dsn = os.getenv('PGRE_DSN', 'postgresql://')


settings = Settings()

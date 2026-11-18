import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is missing. Add it to your .env file.")

    SQLALCHEMY_DATABASE_URI = "sqlite:///nexus.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
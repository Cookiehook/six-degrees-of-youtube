from src.controllers import secrets

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base

engine = create_engine(secrets.get_secret("six-degrees-of-youtube-db-dsn"), future=True)
Base = declarative_base(metadata=MetaData(engine))

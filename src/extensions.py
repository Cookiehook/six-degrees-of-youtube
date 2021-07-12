from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from src.controllers import secrets

engine = create_engine(secrets.get_secret("six-degrees-of-youtube-db-dsn"), poolclass=NullPool)
Base = declarative_base(metadata=MetaData(engine))
session_factory = sessionmaker(bind=engine)

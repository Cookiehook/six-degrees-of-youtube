from flask_sqlalchemy_session import current_session
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import Session

from src.extensions import Base, engine


class UrlLookup(Base):
    """
    Sometimes a given URL will be an old url, which redirects to the new.
    Sometimes a given URL will be a username, which redirects to /user/<url>
    This class stores and resolves these redirects when found, allowing searching through cached API responses
    """
    __tablename__ = "url_lookup"

    original = Column(String, primary_key=True)
    resolved = Column(String)
    is_username = Column(Boolean)

    def __repr__(self):
        return self.original + " - " + self.resolved

    @classmethod
    def get_resolved(cls, url: str) -> str:
        """
        Retrieve the final URL for the given URL, after all redirects have completed.
        If there are no redirects for a given url, the resolved will be the same as the input

        :param url: URL to resolve
        :return: Resolved URL of None
        """
        if lookup := current_session.query(cls).filter(cls.original == url).first():
            return lookup.resolved

    @classmethod
    def url_is_username(cls, url: str) -> bool:
        """
        Check if the given URL resolves to a user, not url attribute.

        :param url: URL to check
        :return: bool if URL found, None if not
        """
        if lookup := current_session.query(cls).filter(cls.original == url).first():
            return lookup.is_username

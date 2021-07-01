from src.extensions import db


class UrlLookup(db.Model):
    """
    Sometimes a given URL will be an old url, which redirects to the new.
    Sometimes a given URL will be a username, which redirects to /user/<url>
    This class stores and resolves these redirects when found, allowing searching through cached API responses
    """
    original = db.Column(db.String, primary_key=True)
    resolved = db.Column(db.String)
    is_username = db.Column(db.Boolean)

    def __init__(self, original: str, resolved: str, is_username: bool = False):
        self.original = original
        self.resolved = resolved
        self.is_username = is_username

        db.session.add(self)
        db.session.commit()

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
        if lookup := cls.query.filter_by(original=url).first():
            return lookup.resolved

    @staticmethod
    def url_is_username(url: str) -> bool:
        """
        Check if the given URL resolves to a user, not url attribute.

        :param url: URL to check
        :return: bool if URL found, None if not
        """
        if lookup := UrlLookup.query.filter_by(original=url).first():
            return lookup.is_username

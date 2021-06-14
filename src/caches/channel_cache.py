from src.enums import ChannelFilters
from src.models.channel import Channel


class ChannelCache:
    collection = []

    @classmethod
    def get_from_cache(cls, identifier_attribute: ChannelFilters, identifier_value) -> Channel:
        if identifier_attribute == ChannelFilters.ID:
            for channel in cls.collection:
                if channel.id == identifier_value:
                    return channel

        if identifier_attribute == ChannelFilters.USERNAME:
            for channel in cls.collection:
                if channel.username == identifier_value:
                    return channel

        if identifier_attribute == ChannelFilters.URL:
            for channel in cls.collection:
                if channel.url == identifier_value:
                    return channel

    @classmethod
    def add(cls, identifier_attribute: ChannelFilters, identifier_value) -> Channel:
        """
        Checks the cache of channels, and retrieves channel from Youtube API if not found.
        Username is a filterable attribute on the API, but it not returned by the API. So if we add by
        username we check the cache for a matching channel ID and set the existing channel's username.

        :param identifier_attribute: Name of attribute to compare
        :param identifier_value: Value of attribute
        :return: Channel instance from cache or Youtube API
        """
        existing_channel = cls.get_from_cache(identifier_attribute, identifier_value)
        if existing_channel:
            return existing_channel

        new_channel = Channel.from_api(identifier_attribute, identifier_value)
        if identifier_attribute == ChannelFilters.USERNAME:
            for existing_channel in cls.collection:
                if existing_channel.id == new_channel.id:
                    existing_channel.username = new_channel.username
                    return existing_channel

        cls.collection.append(new_channel)
        return new_channel


class PartnersCache(ChannelCache):
    collection = []

    @classmethod
    def add(cls, identifier_attribute: ChannelFilters, identifier_value) -> Channel:
        ChannelCache.add(identifier_attribute, identifier_value)
        return super(PartnersCache, cls).add(identifier_attribute, identifier_value)

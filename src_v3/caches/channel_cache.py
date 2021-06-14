from src_v3.enums import ChannelFilters
from src_v3.models.channel import Channel


class ChannelCache:
    collection = []

    def __repr__(self):
        return f"({len(self.collection)}) " + ", ".join([c.title for c in self.collection])

    def get_channel_from_cache(self, identifier_attribute: ChannelFilters, identifier_value):
        if identifier_attribute == ChannelFilters.ID:
            for channel in self.collection:
                if channel.id == identifier_value:
                    return channel

        if identifier_attribute == ChannelFilters.USERNAME:
            for channel in self.collection:
                if channel.username == identifier_value:
                    return channel

        if identifier_attribute == ChannelFilters.URL:
            for channel in self.collection:
                if channel.url == identifier_value:
                    return channel

    def add(self, identifier_attribute: ChannelFilters, identifier_value):
        """
        Checks the cache of channels, and retrieves channel from Youtube API if not found.
        Username is a filterable attribute on the API, but it not returned by the API. So if we add by
        username we check the cache for a matching channel ID and set the existing channel's username.

        :param identifier_attribute: Name of attribute to compare
        :param identifier_value: Value of attribute
        :return: Channel instance from cache or Youtube API
        """
        existing_channel = self.get_channel_from_cache(identifier_attribute, identifier_value)
        if existing_channel:
            return existing_channel

        new_channel = Channel.from_api(identifier_attribute, identifier_value)
        if identifier_attribute == ChannelFilters.USERNAME:
            for existing_channel in self.collection:
                if existing_channel.id == new_channel.id:
                    existing_channel.username = new_channel.username
                    return existing_channel

        self.collection.append(new_channel)
        return new_channel

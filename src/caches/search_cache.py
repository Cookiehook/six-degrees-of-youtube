from src.models.search import Search


class SearchCache:
    collection = {}

    @classmethod
    def get_from_cache(cls, search_id) -> list:
        return cls.collection.get(search_id)

    @classmethod
    def add(cls, search_term, object_types='channel') -> list:
        search_id = f"{search_term} - {object_types}"
        search = cls.get_from_cache(search_id)
        if not search:
            cls.collection[search_id] = Search.from_api(search_term, object_types)
        return cls.get_from_cache(search_id)

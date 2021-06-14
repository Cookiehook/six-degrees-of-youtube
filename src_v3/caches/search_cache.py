from src_v3.models.search import Search


class SearchCache:
    collection = {}

    def get_from_cache(self, search_id):
        return self.collection.get(search_id)

    def add(self, search_term, object_types):
        search_id = f"{search_term} - {object_types}"
        search = self.get_from_cache(search_term)
        if not search:
            self.collection[search_id] = Search.from_api(search_term, object_types)
        return search

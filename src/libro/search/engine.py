from ..model.book import Book, BookFilter
from ..storage.json import JsonDirectoryStorage


class BookSearchEngine:
    def __init__(self, storage: JsonDirectoryStorage[Book]):
        self.storage = storage

    def search(self, filters: BookFilter) -> list[int]:
        match_ids = []
        for book in self.storage.objects:
            if filters.year_min and filters.year_min > book.publish_year:
                continue
            if filters.year_max and filters.year_max < book.publish_year:
                continue
            
            if filters.pages_min and filters.pages_min > book.pages:
                continue
            if filters.pages_max and filters.pages_max < book.pages:
                continue
            
            if filters.include_title and filters.query.lower() in book.title.lower():
                match_ids.append(book.id)
            elif filters.include_author and filters.query.lower() in book.author.full_name().lower():
                match_ids.append(book.id)
            elif filters.include_summary and book.summary is not None and filters.query.lower() in book.summary.lower():
                match_ids.append(book.id)

        return match_ids

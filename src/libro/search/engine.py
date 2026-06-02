from ..model.book import BookEntry, BookFilter
from ..storage.json import JsonIdNumeralStorage


class BookSearchEngine:
    def __init__(self, storage: JsonIdNumeralStorage[BookEntry]):
        self.storage = storage

    def search(self, filters: BookFilter) -> dict[int, BookEntry]:
        matched_books: dict[int, BookEntry] = dict()
        for id, book in self.storage.objects.items():
            if filters.year_min and filters.year_min > book.publish_year:
                continue
            if filters.year_max and filters.year_max < book.publish_year:
                continue

            if filters.pages_min and filters.pages_min > book.pages:
                continue
            if filters.pages_max and filters.pages_max < book.pages:
                continue

            if filters.include_title and filters.query.lower() in book.title.lower():
                matched_books[id] = book
            elif filters.include_author and filters.query.lower() in book.author.full_name().lower():
                matched_books[id] = book
            elif filters.include_summary and book.summary is not None and filters.query.lower() in book.summary.lower():
                matched_books[id] = book

        return matched_books

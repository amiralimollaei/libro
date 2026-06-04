from ..model import BookEntry, BookFilter
from ..storage import JsonIdNumeralStorage, LibroStorage


class BookSearchEngine:
    def search(self, filters: BookFilter) -> dict[int, BookEntry]:
        matched_books: dict[int, BookEntry] = dict()
        for id, book in LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry).objects.items():
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

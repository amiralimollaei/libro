import dataclasses

from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh.query import Or

from ..model.book import Book, BookFilter
from ..storage.paths import LibroPaths


class BookSearchEngine:
    def __init__(self):
        self.index_path = LibroPaths.book_index()
        self.index_path.mkdir(exist_ok=True)

        self.book_schema = Book.get_whoosh_schema()

        # create the index
        self.index = create_in(self.index_path, self.book_schema)

    def add_book(self, book: Book):
        self.add_books([book])

    def add_books(self, books: list[Book]):
        writer = self.index.writer()

        for book in books:
            book_fields = dataclasses.asdict(book)
            book_fields["author"] = book.author.full_name()
            writer.add_document(**book_fields)

        writer.commit()
    
    def remove_book(self, book: Book):
        self.remove_books([book])
    
    def remove_books(self, books: list[Book]):
        writer = self.index.writer()

        for book in books:
            writer.delete_by_term("id", book.id)

        writer.commit()

    def search(self, filters: BookFilter) -> list[int]:
        print(filters.query)
        
        match_any = []
        if filters.include_title:
            match_any.append(QueryParser("title", self.book_schema).parse(filters.query))
        if filters.include_author:
            match_any.append(QueryParser("author", self.book_schema).parse(filters.query))
        if filters.include_summary:
            match_any.append(QueryParser("summary", self.book_schema).parse(filters.query))

        whoosh_query = Or(match_any)
        match_ids = []
        with self.index.searcher() as s:
            results = s.search(whoosh_query)
            for result in results:
                match_ids.append(result.get("id"))

        return match_ids

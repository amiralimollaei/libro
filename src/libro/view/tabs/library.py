from typing import Callable, Optional

import flet as ft

from ..views import BookTile

from ...model.book import Book

SearchPredicateFn = Callable[[Book, str], bool]


class LibraryTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.search_predicate_fn: Optional[SearchPredicateFn] = None
        self.books: list[Book] = []

        self.book_list_view = ft.ListView(expand=True, spacing=10)
        self.search_input = ft.TextField(label="Search Your Library", on_change=self.on_search_change, expand=True)

        self.main_column = ft.Column(
            [
                ft.Row([self.search_input]),
                self.book_list_view,
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def on_search_change(self, e):
        self.book_list_view.controls = []
        for book in self.books:
            if self.search_input.value and not self.search_predicate(book, self.search_input.value):
                continue

            self.book_list_view.controls.append(
                BookTile(book)
            )

    def search_predicate(self, book: Book, query: str) -> bool:
        return self.search_predicate_fn(book, query) if self.search_predicate_fn else True

    def register_search_predicate(self, fn: SearchPredicateFn):
        self.search_predicate_fn = fn

    def update_books(self, books: list[Book]):
        self.books = books

        self.book_list_view.controls = []
        for book in self.books:
            self.book_list_view.controls.append(
                BookTile(book)
            )

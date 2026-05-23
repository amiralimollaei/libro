import flet as ft

from ..views import BookTile

from ...model.book import Book


class LibraryTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.book_list_view = ft.ListView(expand=True, spacing=0, padding=0)

        self.main_column = ft.Column(
            [
                self.book_list_view,
            ],
            expand=True
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def update_books(self, books: list[Book]):
        self.book_list_view.controls = []
        for book in books:
            self.book_list_view.controls.append(
                BookTile(book)
            )

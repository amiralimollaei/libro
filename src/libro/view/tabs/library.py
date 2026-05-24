import flet as ft

from ..views import BookTile

from ...model.book import Book


class LibraryTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.book_list_view = ft.ListView(expand=True, spacing=10)
        self.search_input = ft.TextField(label="Search Your Library", expand=True)

        self.main_column = ft.Column(
            [
                ft.Row([self.search_input]),
                self.book_list_view,
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def update_books(self, books: list[Book]):
        self.book_list_view.controls = []
        for book in books:
            self.book_list_view.controls.append(
                BookTile(book)
            )

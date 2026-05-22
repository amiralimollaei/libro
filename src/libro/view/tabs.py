from typing import Callable

import flet as ft

from ..model.book import Genre, Author, Book


class AddTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.on_save: Callable | None = None

        self.title_input = ft.TextField(label="Book Title", expand=True)
        self.author_first_name_input = ft.TextField(label="Author First Name", expand=True)
        self.author_last_name_input = ft.TextField(label="Author Last Name", expand=True)
        self.pages_input = ft.TextField(label="Pages", keyboard_type=ft.KeyboardType.NUMBER, width=200)
        self.genre_input = ft.Dropdown(
            label="Genre",
            options=[ft.dropdown.Option(e.title()) for e in Genre],
            width=200
        )
        self.summary_input = ft.TextField(label="Book Summary (Optional)", expand=True, multiline=True)
        self.save_button = ft.ElevatedButton(
            "Save to Library",
            icon=ft.icons.Icons.SAVE,
            on_click=self.save,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        )

        self.main_column = ft.Column(
            [
                ft.Row([
                    self.title_input
                ]),
                ft.Row([
                    self.author_first_name_input, self.author_last_name_input, self.pages_input, self.genre_input,

                ]),
                self.summary_input,
                self.save_button,
            ],
            expand=True,
            spacing=20
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def reset(self):
        text_fileds = [
            self.title_input,
            self.author_first_name_input,
            self.author_last_name_input,
            self.pages_input,
            self.summary_input
        ]

        for field in text_fileds:
            field.value = ""

        self.genre_input.value = ""

    def save(self, e):
        return self.on_save(e) if self.on_save else None

    def register_on_save(self, fn: Callable):
        self.on_save = fn

    def get_book_object(self):
        return Book(
            title=self.title_input.value,
            author=Author(
                first_name=self.author_first_name_input.value,
                last_name=self.author_last_name_input.value
            ),
            genre=Genre[self.genre_input.value.title()],  # pyright: ignore[reportOptionalMemberAccess]
            summary=self.summary_input.value
        )


class LibraryTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.book_list_view = ft.ListView(expand=True, spacing=10, padding=20)

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
                ft.Text(book.title)
            )

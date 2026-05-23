from typing import Any, Callable

import flet as ft

from libro.view.views import BookTile

from ...model.reading import ReadingInfo
from ...model.book import Book


ReadingEventFn = Callable[[ReadingInfo, Book], Any]


class ReadingTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.on_book_dismissed_fn: ReadingEventFn | None = None

        self.book_list_view = ft.ListView(expand=True, spacing=0, padding=0)

        self.main_column = ft.Column(
            [
                self.book_list_view,
            ],
            expand=True
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def update_reading_books(self, reading_info_list: list[ReadingInfo], books: list[Book]):
        self.book_list_view.controls = []
        for reading_info in reading_info_list:
            book = next(filter(lambda book: book.id == reading_info.book_id, books))

            self.book_list_view.controls.append(
                self.reading_view(reading_info, book)
            )

    def register_on_book_dismissed_fn(self, fn: ReadingEventFn):
        self.on_book_dismissed_fn = fn

    def on_book_dismissed(self, reading_info: ReadingInfo, book: Book):
        return self.on_book_dismissed_fn(reading_info, book) if self.on_book_dismissed_fn else None

    def reading_view(self, reading_info: ReadingInfo, book: Book):
        def on_dismiss(e):
            self.book_list_view.controls.remove(dismissable)
            self.on_book_dismissed(reading_info, book)

        dismissable = ft.Dismissible(
            dismiss_direction=ft.DismissDirection.HORIZONTAL,
            background=ft.Container(
                ft.Text("Finshed", size=20, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN,
                alignment=ft.Alignment.CENTER_LEFT,
                padding=ft.Padding.symmetric(horizontal=20)
            ),
            secondary_background=ft.Container(
                ft.Text("Give Up", size=20, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED,
                alignment=ft.Alignment.CENTER_RIGHT,
                padding=ft.Padding.symmetric(horizontal=20)
            ),
            on_dismiss=on_dismiss,
            dismiss_thresholds={
                ft.DismissDirection.END_TO_START: 0.2,
                ft.DismissDirection.START_TO_END: 0.2,
            },
            content=BookTile(book, timestamp=reading_info.since_timestamp),
        )

        return dismissable

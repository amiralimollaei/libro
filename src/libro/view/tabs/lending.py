from datetime import datetime
import time

import flet as ft


from ...storage.json import JsonIdNumeralStorage, OnObjectsChangedCtx
from ...storage.paths import LibroPaths
from ...model.book import BookEntry
from ...model.lending import LendingEntry


class LendingBookRow(ft.Row):
    COVER_WIDTH = 80
    COVER_HEIGHT = 120

    def __init__(
        self,
        book: BookEntry,
        book_id: int,
        lending_entry: LendingEntry,
        lending_id: int,
    ):
        super().__init__()

        self.book = book
        self.book_id = book_id

        self.lending_entry = lending_entry
        self.lending_id = lending_id

        is_overdue = (
            lending_entry.returned_time is None
            and lending_entry.due_date < time.time()
        )

        cover_src = LibroPaths.assets() / "placeholder-cover.png"
        if book.cover:
            cover_src = LibroPaths.covers() / book.cover

        cover = ft.Container(
            width=self.COVER_WIDTH,
            height=self.COVER_HEIGHT,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.BLUE_GREY_700,
            content=ft.Image(
                src=str(cover_src)
            )
        )

        due_date = datetime.fromtimestamp(
            lending_entry.due_date
        ).strftime("%Y-%m-%d")

        lent_date = datetime.fromtimestamp(
            lending_entry.lent_date
        ).strftime("%Y-%m-%d")

        status_text = (
            "Overdue"
            if is_overdue
            else "Borrowed"
        )

        status_color = (
            ft.Colors.ERROR
            if is_overdue
            else ft.Colors.PRIMARY
        )

        self.controls = [
            ft.Container(
                expand=True,
                padding=10,
                border_radius=8,
                bgcolor=(
                    ft.Colors.ERROR_CONTAINER
                    if is_overdue
                    else None
                ),
                content=ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        cover,
                        ft.Column(
                            expand=True,
                            spacing=4,
                            controls=[
                                ft.Text(
                                    book.title,
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    book.author.full_name(),
                                    size=14,
                                ),
                                ft.Text(
                                    f"Borrowed by: {lending_entry.borrower.full_name()}",
                                    size=13,
                                ),
                                ft.Text(
                                    f"Lent: {lent_date}",
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                                ft.Text(
                                    f"Due: {due_date}",
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                            ],
                        ),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            controls=[
                                ft.Icon(
                                    ft.Icons.WARNING
                                    if is_overdue
                                    else ft.Icons.PERSON,
                                    color=status_color,
                                ),
                                ft.Text(
                                    status_text,
                                    color=status_color,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
                    ],
                ),
            )
        ]


class LendingTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.lending_storage: JsonIdNumeralStorage[LendingEntry] | None = None
        self.book_storage: JsonIdNumeralStorage[BookEntry] | None = None

        self.lending_list_view = ft.ListView(
            expand=True,
            spacing=10,
        )

        self.main_column = ft.Column(
            [
                self.lending_list_view,
            ],
            expand=True,
            spacing=10,
        )

        super().__init__(
            content=self.main_column,
            **container_kwargs,
        )

    def register_lending_storage(self, storage: JsonIdNumeralStorage[LendingEntry],):
        self.lending_storage = storage
        self.lending_storage.register_change_callback(
            self.on_lending_changed
        )

    def register_book_storage(self, storage: JsonIdNumeralStorage[BookEntry],):
        self.book_storage = storage

    def on_lending_changed(self, ctx: OnObjectsChangedCtx):
        assert self.lending_storage
        self.update_lending_entries(
            self.lending_storage.objects
        )

    def update_lending_entries(
        self,
        entries: dict[int, LendingEntry],
    ):
        assert self.book_storage
        self.lending_list_view.controls = []

        for lending_id, lending_entry in entries.items():
            book_id = lending_entry.book_id
            book = self.book_storage.get(book_id)
            assert book, f"Invalid lending entry, tried to get {book_id=}, but none could be found."
            lending_row = LendingBookRow(
                book=book,
                book_id=book_id,
                lending_entry=lending_entry,
                lending_id=lending_id,
            )

            self.lending_list_view.controls.append(
                lending_row
            )
            pass

        self.update()

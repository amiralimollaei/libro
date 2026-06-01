from datetime import datetime
from typing import Callable, Optional

import flet as ft

from ..storage.paths import LibroPaths
from ..model.book import Book, Genre


# views shared by most tabs

class BookTile(ft.ListTile):
    def __init__(self, book: Book, timestamp: float | None = None):
        self.book = book

        time_fmt = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y, %H:%M:%S") if timestamp else None

        leading = None
        if book.cover and (book_cover_path := LibroPaths.covers() / book.cover).exists():
            leading = ft.Image(str(book_cover_path.absolute()))

        super().__init__(
            leading=leading,
            title=ft.Text(book.title),
            subtitle=ft.Text(book.author.full_name() + (f"\nSince {time_fmt}" if time_fmt else ""), max_lines=2),
            is_three_line=True
        )


class AdvancedSearchFiltersRow(ft.Row):
    def __init__(self, on_filters_change: Callable):
        self.on_filters_change = on_filters_change

        # Year range controls
        self.year_min_input = ft.TextField(
            label="Min Year",
            width=100,
            on_change=self._on_filter_change,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.year_max_input = ft.TextField(
            label="Max Year",
            width=100,
            on_change=self._on_filter_change,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Page count range controls
        self.pages_min_input = ft.TextField(
            label="Min Pages",
            width=100,
            on_change=self._on_filter_change,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.pages_max_input = ft.TextField(
            label="Max Pages",
            width=100,
            on_change=self._on_filter_change,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Genre dropdown
        self.genre_dropdown = ft.Dropdown(
            label="Genre",
            width=150,
            options=[ft.dropdown.Option("Any")] + [ft.dropdown.Option(genre.value) for genre in Genre],
            value="Any",
            on_select=self._on_filter_change
        )

        # Reset button
        self.reset_button = ft.ElevatedButton(
            content="Reset Filters",
            icon=ft.Icons.CLEAR,
            on_click=self._on_reset
        )

        # Filter controls row
        super().__init__(
            [
                ft.Text("Year:", weight=ft.FontWeight.BOLD),
                self.year_min_input,
                ft.Text("to"),
                self.year_max_input,
                ft.Text("Pages:", weight=ft.FontWeight.BOLD),
                self.pages_min_input,
                ft.Text("to"),
                self.pages_max_input,
                self.genre_dropdown,
                self.reset_button,
            ],
            wrap=True,
            spacing=10,
            visible=False,
        )

    @property
    def year_min(self) -> Optional[int]:
        if v := self.year_min_input.value:
            return int(v)

    @property
    def year_max(self) -> Optional[int]:
        if v := self.year_max_input.value:
            return int(v)

    @property
    def pages_min(self) -> Optional[int]:
        if v := self.pages_min_input.value:
            return int(v)

    @property
    def pages_max(self) -> Optional[int]:
        if v := self.pages_max_input.value:
            return int(v)

    def _on_filter_change(self, e):
        self.on_filters_change()

    def _on_reset(self, e):
        self.year_min_input.value = ""
        self.year_max_input.value = ""
        self.pages_min_input.value = ""
        self.pages_max_input.value = ""
        self.genre_dropdown.value = "Any"
        self.update()
        self.on_filters_change()

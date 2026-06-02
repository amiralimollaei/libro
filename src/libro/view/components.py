from datetime import datetime
from typing import Callable, Optional

import flet as ft

from ..callbacks import CallbackMixin, CallbackContext
from ..storage.paths import LibroPaths
from ..model.book import Book, Genre


# views shared by most tabs

class OnBookChangedCtx(CallbackContext):
    id = "on_book_changed"

    def __init__(self, book: Book, book_id: int):
        super().__init__()

        self.book = book
        self.book_id = book_id

    def get_book(self) -> Book:
        return self.book

    def get_book_id(self) -> int:
        return self.book_id


class OnBookRemoveCtx(CallbackContext):
    id = "on_book_remove"

    def __init__(self, book_id: int):
        super().__init__()
        self.book_id = book_id


class BookRow(ft.Dismissible, CallbackMixin):
    COVER_WIDTH = 80
    COVER_HEIGHT = 120

    def __init__(self, book: Book, book_id: int):
        self.__init_callbacks__([
            OnBookChangedCtx.id,
            OnBookRemoveCtx.id
        ])

        self.book = book
        self.book_id = book_id

        self.title = book.title
        self.author = book.author.full_name()
        self.year = book.publish_year
        self.total_pages = book.pages
        self.current_page = book.current_page or 0

        self.progress = (
            self.current_page / self.total_pages
            if self.total_pages > 0
            else 0
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

        self.page_text = ft.Text(f"{self.current_page}/{self.total_pages}")

        self.page_counter_inputs = ft.Row(
            [
                ft.TextButton(
                    content="-10",
                    on_click=self._decrement_page_10,
                ),
                ft.TextButton(
                    content="-1",
                    on_click=self._decrement_page,
                ),
                self.page_text,
                ft.TextButton(
                    content="+1",
                    on_click=self._increment_page,
                ),
                ft.TextButton(
                    content="+10",
                    on_click=self._increment_page_10,
                ),
            ]
        )

        self.progress_text = ft.Text(
            f"{self.progress * 100:.01f}%",
            size=12,
            color=ft.Colors.OUTLINE,
        )
        self.progress_bar = ft.ProgressBar(
            value=self.progress,
            height=8,
            border_radius=4,
            expand=True
        )

        super().__init__(
            content=ft.Row(
                [
                    ft.Container(
                        expand=True,
                        padding=10,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row(
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                    controls=[
                                        cover,
                                        ft.Column(
                                            expand=True,
                                            spacing=4,
                                            controls=[
                                                ft.Text(
                                                    self.title,
                                                    size=18,
                                                    weight=ft.FontWeight.BOLD,
                                                    max_lines=2,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                ),
                                                ft.Text(
                                                    self.author,
                                                    size=14,
                                                ),
                                                ft.Text(
                                                    str(self.year),
                                                    size=13,
                                                    color=ft.Colors.OUTLINE,
                                                ),
                                            ],
                                        ),
                                        ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.END,
                                            controls=[
                                                self.page_counter_inputs
                                            ],
                                        ),
                                    ],
                                ),
                                ft.Row([
                                    self.progress_text,
                                    self.progress_bar,
                                ], expand=True),
                            ],
                        ),
                    )
                ],
                expand = True
            ),
            dismiss_direction=ft.DismissDirection.END_TO_START,
            background=ft.Container(
                bgcolor=ft.Colors.RED,
                alignment=ft.Alignment.CENTER_RIGHT,
                padding=20,
                content=ft.Icon(
                    ft.Icons.DELETE,
                    color=ft.Colors.WHITE,
                ),
            ),
        )

    def register_on_book_changed(self, fn: Callable[[OnBookChangedCtx], None]):
        self.register_callback(OnBookChangedCtx.id, fn)

    def register_on_book_remove(self, fn: Callable[[OnBookRemoveCtx], None]):
        self.register_callback(OnBookRemoveCtx.id, fn)

    def _increment_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _increment_page_10(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 10
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _decrement_page(self, e):
        if self.current_page > 0:
            self.current_page -= 1
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _decrement_page_10(self, e):
        if self.current_page > 0:
            self.current_page -= 10
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _refresh_progress(self):
        self.progress = (
            self.current_page / self.total_pages
            if self.total_pages > 0
            else 0
        )

        self.page_text.value = f"{self.current_page}/{self.total_pages}"
        self.progress_text.value = f"{self.progress * 100:.01f}%"
        self.progress_bar.value = self.progress
        self._run_callbacks(OnBookChangedCtx(self.book, self.book_id))

        self.update()


class AdvancedSearchFiltersColumn(ft.Column):
    def __init__(self, on_filters_change: Callable):
        self.on_filters_change = on_filters_change

        # Year range controls
        self.year_min_input = ft.TextField(
            label="Min Year",
            width=120,
            on_change=self._on_filter_change,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.year_max_input = ft.TextField(
            label="Max Year",
            width=120,
            on_change=self._on_filter_change,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Page count range controls
        self.pages_min_input = ft.TextField(
            label="Min Pages",
            width=120,
            on_change=self._on_filter_change,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.pages_max_input = ft.TextField(
            label="Max Pages",
            width=120,
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
                ft.Row([
                    self.year_min_input,
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=16),
                    self.year_max_input,
                ]),
                ft.Text("Pages:", weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.pages_min_input,
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=16),
                    self.pages_max_input,
                ]),
                self.genre_dropdown,
                self.reset_button,
            ],
            wrap=True,
            spacing=10
        )

    def _parse_int(self, value: str) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @property
    def year_min(self) -> Optional[int]:
        return self._parse_int(self.year_min_input.value)

    @property
    def year_max(self) -> Optional[int]:
        return self._parse_int(self.year_max_input.value)

    @property
    def pages_min(self) -> Optional[int]:
        return self._parse_int(self.pages_min_input.value)

    @property
    def pages_max(self) -> Optional[int]:
        return self._parse_int(self.pages_max_input.value)

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

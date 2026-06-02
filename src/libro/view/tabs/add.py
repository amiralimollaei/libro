import re
from datetime import datetime
from typing import Callable

import flet as ft

from ...callbacks import CallbackMixin, CallbackContext
from ...storage.paths import LibroPaths
from ...model.book import Genre, Person, BookEntry


class OnAddBookCtx(CallbackContext):
    id = "on_add_book"

    def __init__(self, event: ft.Event):
        super().__init__()
        self.event = event

    def get_event(self):
        return self.event


class AddTab(ft.Container, CallbackMixin):
    def __init__(self, **container_kwargs):
        # initialize our callbacks for the CallbackMixin
        self.__init_callbacks__([
            "on_add_book",
        ])

        self.title_input = ft.TextField(
            label="Book Title",
            on_change=self.validate_title_input,
            expand=True
        )
        self.author_first_name_input = ft.TextField(
            label="Author First Name",
            on_change=self.validate_first_name_input,
            expand=True
        )
        self.author_last_name_input = ft.TextField(
            label="Author Last Name",
            on_change=self.validate_last_name_input,
            expand=True
        )
        self.genre_input = ft.Dropdown(
            label="Genre",
            on_select=self.validate_genre_input,
            options=[
                ft.dropdown.Option(
                    key=genre.value,
                    text=genre.label
                )
                for genre in Genre
            ],
            width=160
        )
        self.pages_input = ft.TextField(
            label="Pages",
            on_change=self.validate_pages_input,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=160
        )
        self.publish_year_input = ft.TextField(
            label="Publish Year",
            on_change=self.validate_publish_year_input,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=160
        )
        self.summary_input = ft.TextField(
            label="Book Summary (Optional)",
            expand=True,
            multiline=True
        )

        async def book_cover_pick(e):
            book_cover_file_picker = ft.FilePicker()
            picked_files = await book_cover_file_picker.pick_files(file_type=ft.FilePickerFileType.IMAGE)
            if picked_files and picked_files[0].path:
                self.book_cover_preview.src = picked_files[0].path

        self.book_cover_input = ft.Button(
            content="Pick Cover",
            on_click=book_cover_pick,
            expand=False
        )

        self.book_cover_preview = ft.Image(
            src=str(LibroPaths.assets().absolute() / "placeholder-cover.png"),
            width=160,
            expand=True
        )

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
                    self.author_first_name_input, self.author_last_name_input, self.pages_input, self.publish_year_input, self.genre_input,
                ]),
                ft.Row(
                    [
                        self.summary_input,
                        ft.Column(
                            [self.book_cover_preview, self.book_cover_input],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                ),
                self.save_button,
            ],
            expand=True,
            spacing=10
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def validate_title_input(self, e):
        self.title_input.border_color = None

    def validate_first_name_input(self, e):
        self.author_first_name_input.border_color = None

    def validate_last_name_input(self, e):
        self.author_last_name_input.border_color = None

    def validate_genre_input(self, e):
        self.genre_input.border_color = None

    def validate_pages_input(self, e):
        self.pages_input.value = re.sub(r'[^\d]', '', self.pages_input.value)
        try:
            int(self.pages_input.value)
            self.pages_input.border_color = None
        except Exception:
            self.pages_input.border_color = ft.Colors.ERROR

    def validate_publish_year_input(self, e):
        self.publish_year_input.value = re.sub(r'[^\d]', '', self.publish_year_input.value)
        try:
            year_num = int(self.publish_year_input.value)
            assert year_num < datetime.now().year
            self.publish_year_input.border_color = None
        except Exception:
            self.publish_year_input.border_color = ft.Colors.ERROR

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
        if not self.title_input.value:
            self.title_input.border_color = ft.Colors.ERROR
        if not self.author_first_name_input.value:
            self.author_first_name_input.border_color = ft.Colors.ERROR
        if not self.author_last_name_input.value:
            self.author_last_name_input.border_color = ft.Colors.ERROR
        if not self.genre_input.value:
            self.genre_input.border_color = ft.Colors.ERROR
        if not self.pages_input.value:
            self.pages_input.border_color = ft.Colors.ERROR
        if not self.publish_year_input.value:
            self.publish_year_input.border_color = ft.Colors.ERROR
        self.update()

        ctx = self._run_callbacks(OnAddBookCtx(event=e))

        return ctx.result

    def register_on_add_book_fn(self, fn: Callable):
        """alias for `self.register_callback("on_add_book", fn)`"""
        self.register_callback("on_add_book", fn)

    def get_book_object(self):
        return BookEntry(
            title=self.title_input.value,
            author=Person(
                first_name=self.author_first_name_input.value,
                last_name=self.author_last_name_input.value
            ),
            genre=Genre(self.genre_input.value), # pyright: ignore[reportArgumentType]
            pages=int(self.pages_input.value),
            publish_year=int(self.publish_year_input.value),
            summary=self.summary_input.value,
            cover=self.book_cover_preview.src  # pyright: ignore[reportArgumentType]
        )

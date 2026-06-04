from datetime import date, datetime, time
from typing import Callable

import flet as ft

from ...callbacks import CallbackContext, CallbackMixin
from ...model import Genre


class DialogClosedCtx(CallbackContext):
    id = "on_dialog_closed"


class AdvancedSearchDialog(ft.AlertDialog, CallbackMixin):
    def __init__(self, on_filters_change: Callable[[ft.Event], None]):
        self.__init_callbacks__([
            DialogClosedCtx.id
        ])

        self.on_filters_change = on_filters_change

        self.year_min_input = ft.TextField(
            label="Minimum Year",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.year_max_input = ft.TextField(
            label="Maximum Year",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.pages_min_input = ft.TextField(
            label="Minimum Pages",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.pages_max_input = ft.TextField(
            label="Maximum Pages",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.genre_dropdown = ft.Dropdown(
            label="Genre",
            value="Any",
            options=[
                ft.dropdown.Option("Any"),
                *[
                    ft.dropdown.Option(genre.label)
                    for genre in Genre
                ]
            ],
            on_select=self._on_filter_change,
        )

        super().__init__(
            modal=False,
            title=ft.Text(
                "Advanced Filters",
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    controls=[
                        self.genre_dropdown,

                        self.year_min_input,
                        self.year_max_input,

                        self.pages_min_input,
                        self.pages_max_input,
                    ],
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Reset",
                    icon=ft.Icons.CLEAR,
                    on_click=self._on_reset,
                ),
                ft.FilledButton(
                    "Close",
                    on_click=self._close,
                ),
            ],
        )
        
    def _close(self, e):
        self.page.pop_dialog()
        self._run_callbacks(DialogClosedCtx())

    def _parse_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @property
    def year_min(self):
        return self._parse_int(self.year_min_input.value)

    @property
    def year_max(self):
        return self._parse_int(self.year_max_input.value)

    @property
    def pages_min(self):
        return self._parse_int(self.pages_min_input.value)

    @property
    def pages_max(self):
        return self._parse_int(self.pages_max_input.value)

    @property
    def genre(self):
        if self.genre_dropdown.value == "Any":
            return None
        return self.genre_dropdown.value

    def reset(self):
        self.year_min_input.value = ""
        self.year_max_input.value = ""
        self.pages_min_input.value = ""
        self.pages_max_input.value = ""
        self.genre_dropdown.value = "Any"
    
    def _on_filter_change(self, e):
        self.on_filters_change(e)

    def _on_reset(self, e):
        self.reset()
        self.update()
        self.on_filters_change(e)

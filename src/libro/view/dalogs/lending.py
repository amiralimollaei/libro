from datetime import date, datetime, time
from typing import Callable

import flet as ft

from ...callbacks import CallbackContext, CallbackMixin


class DialogClosedCtx(CallbackContext):
    id = "on_dialog_closed"


class LendingDialog(ft.AlertDialog, CallbackMixin):
    def __init__(self, book_title: str, on_submit: 'Callable[[LendingDialog], None] | None' = None):
        self.__init_callbacks__([
            DialogClosedCtx.id
        ])

        self.borrower_input = ft.TextField(
            label="Borrower",
            autofocus=True,
            expand=True
        )

        self.note_input = ft.TextField(
            label="Notes",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True
        )

        self.return_date_field = ft.TextField(
            label="Return Date",
            read_only=True,
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            on_click=self._pick_date,
            expand=True
        )

        self.return_time_field = ft.TextField(
            label="Return Time",
            read_only=True,
            suffix_icon=ft.Icons.ACCESS_TIME,
            on_click=self._pick_time,
            expand=True
        )

        self.selected_date: date | None = None
        self.selected_time: time | None = None

        self.date_picker = ft.DatePicker(
            first_date=datetime.today(),
            on_change=self._on_date_selected,
        )

        self.time_picker = ft.TimePicker(
            on_change=self._on_time_selected,
        )

        self.on_submit: Callable[[LendingDialog], None] | None = on_submit

        super().__init__(
            modal=True,
            title=ft.Text(f"Lend '{book_title}'"),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    [
                        ft.Row([self.borrower_input]),
                        ft.Row([self.return_date_field, self.return_time_field]),
                        ft.Row([self.note_input]),
                    ],
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._close,
                ),
                ft.FilledButton(
                    "Lend",
                    icon=ft.Icons.PERSON_ADD,
                    on_click=self._submit,
                ),
            ],
        )

    @property
    def borrower(self) -> str:
        return self.borrower_input.value.strip()

    @property
    def due_at(self) -> datetime | None:
        if self.selected_date is None:
            return None

        if self.selected_time is None:
            return None

        return datetime.combine(
            self.selected_date,
            self.selected_time,
        )

    @property
    def note(self) -> str:
        return self.note_input.value.strip()

    def _pick_date(self, e):
        self.page.show_dialog(self.date_picker)

    def _pick_time(self, e):
        self.page.show_dialog(self.time_picker)

    def _on_date_selected(self, e):
        self.selected_date = e.control.value.date()

        self.return_date_field.value = self.selected_date.isoformat()  # pyright: ignore[reportOptionalMemberAccess]

        self.update()

    def _on_time_selected(self, e):
        t = e.control.value

        self.selected_time = time(
            hour=t.hour,
            minute=t.minute,
        )

        self.return_time_field.value = (
            self.selected_time.strftime("%H:%M")
        )

        self.update()

    def _close(self, e):
        self.page.pop_dialog()
        self._run_callbacks(DialogClosedCtx())

    def _submit(self, e):
        if not self.borrower:
            self.borrower_input.error = "Borrower is required"
            self.update()
            return

        if self.on_submit:
            self.on_submit(self)

        self._close(e)

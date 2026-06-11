"""Dialog for editing the due date of a lending entry.

This dialog was extracted from ``LendingController.on_lending_edit_due`` to keep the
controller focused on business logic and to reuse the UI component elsewhere if
needed.
"""

from datetime import datetime, date, time
from typing import Callable

import flet as ft

from ...callbacks import CallbackContext, CallbackMixin


class EditDueDateClosedCtx(CallbackContext):
    """Callback context emitted when the dialog is closed without saving."""

    id = "on_edit_due_date_closed"


class EditDateTimeDialog(ft.AlertDialog, CallbackMixin):
    """
    A dialog that allows the user to pick a new due date and time.
    """

    def __init__(
        self,
        current_due: datetime,
        on_submit: Callable[[datetime], None] | None = None,
    ) -> None:
        self.__init_callbacks__([EditDueDateClosedCtx.id])

        self._on_submit = on_submit

        self._selected_date: date = current_due.date()
        self._selected_time: time = current_due.time()

        self._date_field = ft.TextField(
            label="Due Date",
            read_only=True,
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            value=self._selected_date.isoformat(),
            on_click=lambda e: self.page.show_dialog(self._date_picker),
        )
        self._time_field = ft.TextField(
            label="Due Time",
            read_only=True,
            suffix_icon=ft.Icons.ACCESS_TIME,
            value=self._selected_time.strftime("%H:%M"),
            on_click=lambda e: self.page.show_dialog(self._time_picker),
        )

        # Pickers – they are attached to the page overlay later
        self._date_picker = ft.DatePicker(
            first_date=datetime.today(),
            value=current_due,
            on_change=self._on_date_selected,
        )
        self._time_picker = ft.TimePicker(
            value=current_due.time(),
            on_change=self._on_time_selected,
        )

        # Build the dialog UI
        super().__init__(
            modal=True,
            title=ft.Text("Edit Due Date"),
            content=ft.Column(
                [ft.Column([self._date_field, self._time_field])],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.FilledButton(
                    "Save",
                    icon=ft.Icons.SAVE,
                    on_click=self._on_save,
                ),
            ],
        )

    def _on_date_selected(self, e: ft.ControlEvent) -> None:
        """Update the stored date and UI when the user picks a new date."""
        if e.control.value:
            self._selected_date = e.control.value.date()
            self._date_field.value = self._selected_date.isoformat()
            self._date_field.update()

    def _on_time_selected(self, e: ft.ControlEvent) -> None:
        """Update the stored time and UI when the user picks a new time."""
        if e.control.value:
            t = e.control.value
            self._selected_time = time(hour=t.hour, minute=t.minute)
            self._time_field.value = self._selected_time.strftime("%H:%M")
            self._time_field.update()

    def _on_cancel(self, e: ft.ControlEvent) -> None:
        """Close the dialog without saving and emit the closed callback."""
        self.page.pop_dialog()
        self._run_callbacks(EditDueDateClosedCtx())

    def _on_save(self, e: ft.ControlEvent) -> None:
        """Combine the selected date and time, invoke the submit callback, and close."""
        new_due = datetime.combine(self._selected_date, self._selected_time)
        if self._on_submit:
            self._on_submit(new_due)
        self.page.pop_dialog()

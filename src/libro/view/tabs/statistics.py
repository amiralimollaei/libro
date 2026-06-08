from datetime import datetime, timezone
from typing import Optional

import flet as ft

from ...model import PagesInLentPeriodEntry, Statistics
from ...storage import JsonFileStorage, LibroStorage, OnObjectsChangedCtx
from .base import AbstractTab


class StatCard(ft.Container):
    """A reusable card for displaying a single statistic with label and value."""

    def __init__(
        self,
        label: str,
        value: str,
        icon: ft.IconData,
        color: ft.Colors = ft.Colors.PRIMARY,
    ):
        self._value_text = ft.Text(
            value,
            size=24,
            weight=ft.FontWeight.BOLD,
            color=color,
            text_align=ft.TextAlign.CENTER,
        )
        super().__init__(
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, color=color, size=28),
                    self._value_text,
                    ft.Text(
                        label,
                        size=12,
                        color=ft.Colors.OUTLINE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def set_value(self, value: str):
        """Update the displayed numeric value of this stat card."""
        self._value_text.value = value


class PeriodList(ft.Container):
    """A compact list showing period-based data in a scrollable format."""

    def __init__(self, title: str, empty_message: str = "No data yet"):
        self.title_text = ft.Text(title, size=16, weight=ft.FontWeight.BOLD)
        self.list_view = ft.ListView(
            expand=True,
            spacing=4,
        )
        self.empty_text = ft.Text(
            empty_message,
            color=ft.Colors.OUTLINE,
            italic=True,
        )

        super().__init__(
            expand=True,
            content=ft.Column(
                spacing=8,
                controls=[
                    self.title_text,
                    ft.Container(
                        expand=True,
                        content=self.list_view,
                    ),
                ],
            ),
        )

    def update_items(self, items: list[ft.Control]):
        """Replace the list content with new items."""
        self.list_view.controls = items if items else [self.empty_text]


def _format_month_key(month_key: str) -> str:
    """Convert 'YYYY-MM' to a human-readable 'Mon YYYY' format."""
    try:
        dt = datetime.strptime(month_key, "%Y-%m")
        return dt.strftime("%b %Y")
    except (ValueError, TypeError):
        return month_key


def _format_date_key(date_key: str) -> str:
    """Convert 'YYYY-MM-DD' to a human-readable 'Mon DD, YYYY' format."""
    try:
        dt = datetime.strptime(date_key, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return date_key


class StatisticsTab(AbstractTab):
    """Tab displaying general library statistics."""

    def __init__(self, **container_kwargs):
        self._build_ui()

        super().__init__(
            content=self.main_column,
            **container_kwargs,
        )

        # auto-refresh whenever the statistics cache changes
        stats_storage: JsonFileStorage[Statistics] = LibroStorage.get(
            JsonFileStorage[Statistics], Statistics
        )
        stats_storage.register_change_callback(self._on_stats_changed)

    def register_page(self, page: ft.Page):
        self._refresh_data()

    def _build_ui(self):
        # overview cards row
        self.total_books_card = StatCard(
            "Books Finished", "—", ft.Icons.AUTO_STORIES, ft.Colors.TERTIARY
        )
        self.total_pages_card = StatCard(
            "Pages Read", "—", ft.Icons.MENU_BOOK, ft.Colors.PRIMARY
        )
        self.books_lent_card = StatCard(
            "Books Lent", "—", ft.Icons.OUTBOX, ft.Colors.ERROR
        )
        self.overdue_card = StatCard(
            "Overdue", "—", ft.Icons.WARNING, ft.Colors.ERROR
        )

        cards_row = ft.ResponsiveRow(
            controls=[
                ft.Container(col={"xs": 6, "sm": 3, "md": 3, "lg": 3, "xl": 3}, content=self.total_books_card),
                ft.Container(col={"xs": 6, "sm": 3, "md": 3, "lg": 3, "xl": 3}, content=self.total_pages_card),
                ft.Container(col={"xs": 6, "sm": 3, "md": 3, "lg": 3, "xl": 3}, content=self.books_lent_card),
                ft.Container(col={"xs": 6, "sm": 3, "md": 3, "lg": 3, "xl": 3}, content=self.overdue_card),
            ],
            spacing=10,
        )

        # period sections 
        self.pages_read_list = PeriodList(
            "Pages Read (Daily)", "No reading recorded yet."
        )
        self.books_finished_list = PeriodList(
            "Books Finished (Monthly)", "No books finished yet."
        )
        self.books_lent_list = PeriodList(
            "Books Lent (Monthly)", "No books lent yet."
        )
        self.lending_status_list = PeriodList(
            "Lending Status", "No lending activity yet."
        )

        # Layout: two columns for period data
        period_row = ft.ResponsiveRow(
            controls=[
                ft.Container(col={"sm": 12, "md": 6}, content=self.pages_read_list),
                ft.Container(col={"sm": 12, "md": 6}, content=self.books_finished_list),
                ft.Container(col={"sm": 12, "md": 6}, content=self.books_lent_list),
                ft.Container(col={"sm": 12, "md": 6}, content=self.lending_status_list),
            ],
            spacing=10,
        )

        self.main_column = ft.Column(
            controls=[
                ft.Text(
                    "Library Statistics",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                cards_row,
                ft.Divider(),
                period_row,
            ],
            expand=True,
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )

    def _on_stats_changed(self, ctx: OnObjectsChangedCtx):
        self._refresh_data()

    def _refresh_data(self):
        """Load the statistics cache and update all UI elements."""
        stats_storage: JsonFileStorage[Statistics] = LibroStorage.get(
            JsonFileStorage[Statistics], Statistics
        )
        stats = stats_storage.get()

        if stats is None:
            self._show_empty()
            return

        self._update_cards(stats)
        self._update_pages_read(stats)
        self._update_books_finished(stats)
        self._update_books_lent(stats)
        self._update_lending_status(stats)
        self.update()

    def _show_empty(self):
        """Display empty state for all stats."""
        self.total_books_card.set_value("—")
        self.total_pages_card.set_value("—")
        self.books_lent_card.set_value("—")
        self.overdue_card.set_value("—")
        self.pages_read_list.update_items([])
        self.books_finished_list.update_items([])
        self.books_lent_list.update_items([])
        self.lending_status_list.update_items([])
        self.update()

    def _update_cards(self, stats: Statistics):
        """Update the overview cards."""
        total_finished = sum(
            entry.count for entry in stats.books_finished_by_period.values()
        )
        total_pages = sum(
            entry.pages for entry in stats.pages_read_by_period.values()
        )
        total_lent = sum(
            entry.count for entry in stats.books_lent_by_period.values()
        )
        overdue_count = sum(
            1 for entry in stats.lending_status.values()
            if entry.status == "returned_overdue"
        )

        self.total_books_card.set_value(str(total_finished))
        self.total_pages_card.set_value(str(total_pages))
        self.books_lent_card.set_value(str(total_lent))
        self.overdue_card.set_value(str(overdue_count))

    def _update_pages_read(self, stats: Statistics):
        """Update the daily pages-read list."""
        items: list[ft.Control] = []

        # show most recent first (sorted descending)
        sorted_dates = sorted(
            stats.pages_read_by_period.keys(), reverse=True
        )
        for date_key in sorted_dates[:20]:  # limit to last 20 entries
            entry = stats.pages_read_by_period[date_key]
            items.append(
                ft.ListTile(
                    title=ft.Text(
                        _format_date_key(date_key),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    subtitle=ft.Text(
                        f"{entry.pages} pages" if entry.pages == 1 else f"{entry.pages} pages",
                        size=13,
                    ),
                    leading=ft.Icon(ft.Icons.BOOK,
                                    color=ft.Colors.PRIMARY),
                    dense=True,
                )
            )
        self.pages_read_list.update_items(items)

    def _update_books_finished(self, stats: Statistics):
        """Update the monthly books-finished list."""
        items: list[ft.Control] = []
        sorted_months = sorted(
            stats.books_finished_by_period.keys(), reverse=True
        )
        for month_key in sorted_months:
            entry = stats.books_finished_by_period[month_key]
            items.append(
                ft.ListTile(
                    title=ft.Text(
                        _format_month_key(month_key),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    subtitle=ft.Text(
                        f"{entry.count} book{'s' if entry.count != 1 else ''}",
                        size=13,
                    ),
                    leading=ft.Icon(ft.Icons.AUTO_STORIES,
                                    color=ft.Colors.TERTIARY),
                    dense=True,
                )
            )
        self.books_finished_list.update_items(items)

    def _update_books_lent(self, stats: Statistics):
        """Update the monthly books-lent list."""
        items: list[ft.Control] = []
        sorted_months = sorted(
            stats.books_lent_by_period.keys(), reverse=True
        )
        for month_key in sorted_months:
            lent_entry = stats.books_lent_by_period[month_key]
            pages_entry: Optional[PagesInLentPeriodEntry] = (
                stats.pages_in_lent_by_period.get(month_key)
            )
            subtitle = f"{lent_entry.count} book{'s' if lent_entry.count != 1 else ''}"
            if pages_entry:
                subtitle += f" · avg {pages_entry.avg_pages_per_book:.0f} pages/book"
            items.append(
                ft.ListTile(
                    title=ft.Text(
                        _format_month_key(month_key),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    subtitle=ft.Text(subtitle, size=13),
                    leading=ft.Icon(ft.Icons.OUTBOX,
                                    color=ft.Colors.ERROR),
                    dense=True,
                )
            )
        self.books_lent_list.update_items(items)

    def _update_lending_status(self, stats: Statistics):
        """Update the lending status list."""
        items: list[ft.Control] = []

        # show most recent first
        sorted_lend_ids = sorted(
            stats.lending_status.keys(), reverse=True
        )[:20]
        for lend_id in sorted_lend_ids:
            entry = stats.lending_status[lend_id]
            return_dt = datetime.fromtimestamp(
                entry.return_date, tz=timezone.utc
            ).strftime("%Y-%m-%d")

            if entry.status == "returned_overdue":
                icon = ft.Icons.WARNING
                color = ft.Colors.ERROR
                subtitle = f"Overdue by {entry.overdue_days} days · Returned {return_dt}"
            else:
                icon = ft.Icons.CHECK_CIRCLE
                color = ft.Colors.PRIMARY
                subtitle = f"Returned on time · {return_dt}"

            items.append(
                ft.ListTile(
                    title=ft.Text(
                        f"Lending #{lend_id}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    subtitle=ft.Text(subtitle, size=13),
                    leading=ft.Icon(icon, color=color),
                    dense=True,
                )
            )
        self.lending_status_list.update_items(items)

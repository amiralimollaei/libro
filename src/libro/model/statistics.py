import dataclasses
from datetime import datetime
from typing import Optional

import dataclasses_json

from ..storage.json import StorableObject


# ---- Event Dataclasses ----


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class BookReadEvent:
    """Event when user reads pages of a book"""
    pages_read: int
    previous_pages_read: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class BookFinishedEvent:
    """Event when user finishes reading a book"""
    total_pages: int
    # calendar days from first read to finish (time delta, in days)
    days_to_finish: float
    # number of unique days with reading progress
    active_days_to_finish: int = 0


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class BookLentEvent:
    """Event when a book is lent out"""
    lend_id: int
    total_pages: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class BookReturnedEvent:
    """Event when a lent book is returned"""
    lend_id: int
    overdue_time: Optional[float] = None  # None if on time, otherwise seconds overdue


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class StatisticalEvent(StorableObject):
    """Container for any statistical event. Exactly one event field is populated."""
    book_id: int
    timestamp: float

    book_read: Optional[BookReadEvent] = None
    book_finished: Optional[BookFinishedEvent] = None
    book_lent: Optional[BookLentEvent] = None
    book_returned: Optional[BookReturnedEvent] = None


# ---- Period Entry Models ----
# These replace bare dict types in Statistics fields, providing type safety
# and self-documenting schemas for the serialized JSON data.


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class PagesReadPeriodEntry:
    """
    Number of pages read for a given period (daily).
    Wrapped in a model class to allow future extensibility.
    """
    pages: int = 0


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class MonthBookEntry:
    """
    Count and list of book IDs for a given month.
    Reused for both finished-books and lent-books period aggregation.
    """
    count: int = 0
    book_ids: list[int] = dataclasses.field(default_factory=list)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class PagesInLentPeriodEntry:
    """
    Total pages lent out and the average pages-per-book for a given month.
    """
    total_pages: int = 0
    avg_pages_per_book: float = 0.0


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class LendingStatusEntry:
    """
    Status of a single lending record.
    """
    status: str = ""
    return_date: float = 0.0
    overdue_days: int = 0


# ---- Deprecated (kept for migration compatibility) ----


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class BookIdStatistics:
    book_id: int  # the ID of this book in our library


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Statistics(StorableObject):
    """Cache of precomputed statistical aggregates (daily/weekly/monthly)"""
    # period-based aggregates: dict[date_str] = {...}
    books_finished_by_period: dict[str, MonthBookEntry] = dataclasses.field(default_factory=dict)
    pages_read_by_period: dict[str, PagesReadPeriodEntry] = dataclasses.field(default_factory=dict)
    books_lent_by_period: dict[str, MonthBookEntry] = dataclasses.field(default_factory=dict)
    pages_in_lent_by_period: dict[str, PagesInLentPeriodEntry] = dataclasses.field(default_factory=dict)
    lending_status: dict[int, LendingStatusEntry] = dataclasses.field(default_factory=dict)  # lend_id -> status

    # Metadata
    books_dismissed: list[BookIdStatistics] = dataclasses.field(default_factory=list)
    last_updated_timestamp: float = 0.0


# ---- History Entry for Book-Level Weekly/Monthly Charts ----


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class PeriodHistoryEntry:
    """
    A single data point in a book's reading history.
    label is a short human-readable string (e.g. "Jun 1", "Week 23", "May").
    """
    label: str
    pages: int


@dataclasses.dataclass
class BookStatisticsModel:
    """
    Model for displaying book reading statistics in the UI.

    Holds computed statistics about a book's reading progress,
    including per-day averages and weekly/monthly aggregates with
    history data for chart display.
    """
    book_id: int
    pages_read_per_day: Optional[float] = None
    days_reading: Optional[int] = None

    # Weekly/Monthly aggregate pages
    this_week_pages: Optional[int] = None
    this_month_pages: Optional[int] = None
    last_month_pages: Optional[int] = None

    # Weekly/Monthly progress percentage (of total book pages)
    this_week_progress: Optional[float] = None
    this_month_progress: Optional[float] = None

    # History data for bar chart display
    weekly_history: list[PeriodHistoryEntry] = dataclasses.field(default_factory=list)
    monthly_history: list[PeriodHistoryEntry] = dataclasses.field(default_factory=list)

    def get_pages_read_per_day_display(self) -> str:
        """Get formatted string for pages read per day."""
        if self.pages_read_per_day is None:
            return "— pages/day"
        return f"{self.pages_read_per_day:.2f} pages/day"

    def get_days_reading_display(self) -> str:
        """Get formatted string for days spent reading."""
        if self.days_reading is None:
            return "— days"
        return f"{self.days_reading} days"

    def get_this_week_pages_display(self) -> str:
        """Get formatted string for this week's pages."""
        if self.this_week_pages is None:
            return "—"
        return f"{self.this_week_pages} pages"

    def get_this_month_pages_display(self) -> str:
        """Get formatted string for this month's pages."""
        if self.this_month_pages is None:
            return "—"
        return f"{self.this_month_pages} pages"

    def get_last_month_pages_display(self) -> str:
        """Get formatted string for last month's pages."""
        if self.last_month_pages is None:
            return "—"
        return f"{self.last_month_pages} pages"

    def get_this_week_progress_display(self) -> str:
        """Get formatted string for this week's progress percentage."""
        if self.this_week_progress is None:
            return "—"
        return f"{self.this_week_progress * 100:.1f}%"

    def get_this_month_progress_display(self) -> str:
        """Get formatted string for this month's progress percentage."""
        if self.this_month_progress is None:
            return "—"
        return f"{self.this_month_progress * 100:.1f}%"

    def get_monthly_comparison_display(self) -> str:
        """Get formatted string comparing this month to last month."""
        if self.last_month_pages is None or self.last_month_pages == 0:
            if self.this_month_pages is not None:
                return f"+{self.this_month_pages} pages (new)"
            return "—"
        if self.this_month_pages is None:
            return "—"
        diff = self.this_month_pages - self.last_month_pages
        pct = (diff / self.last_month_pages) * 100
        if diff >= 0:
            return f"↑ +{diff} pages (+{pct:.0f}%)"
        else:
            return f"↓ {diff} pages ({pct:.0f}%)"
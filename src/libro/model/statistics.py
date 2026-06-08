import dataclasses
from datetime import datetime
from typing import Optional

import dataclasses_json

from ..storage.json import StorableObject


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class ReadBookStatistics:
    book_id: int  # the ID of this book in our library
    begin_time: float  # the time the user began reading the book
    finish_time: float  # the time the user finished reading the book


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class LendBookStatistics:
    book_id: int  # the ID of this book in our library
    begin_time: float  # the time the user began reading the book
    finish_time: float  # the time the user finished reading the book


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class BookIdStatistics:
    book_id: int  # the ID of this book in our library


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Statistics(StorableObject):
    book_reading_sessions: list[ReadBookStatistics]
    book_lending_sessions: list[LendBookStatistics]
    books_dismissed: list[BookIdStatistics]


@dataclasses.dataclass
class BookStatisticsModel:
    """
    Model for displaying book reading statistics in the UI.

    This class holds computed statistics about a book's reading progress
    such as pages read per day, progress per day, and estimated finish date.
    """
    book_id: int
    pages_read_per_day: Optional[float] = None
    progress_per_day: Optional[float] = None
    estimated_finish_date: Optional[datetime] = None
    days_reading: Optional[int] = None
    total_reading_time_hours: Optional[float] = None

    def get_pages_read_per_day_display(self) -> str:
        """Get formatted string for pages read per day."""
        if self.pages_read_per_day is None:
            return "— pages/day"
        return f"{self.pages_read_per_day:.2f} pages/day"

    def get_progress_per_day_display(self) -> str:
        """Get formatted string for progress per day."""
        if self.progress_per_day is None:
            return "— %/day"
        return f"{self.progress_per_day:.2f} %/day"

    def get_estimated_finish_date_display(self) -> str:
        """Get formatted string for estimated finish date."""
        if self.estimated_finish_date is None:
            return "— "
        return self.estimated_finish_date.strftime("%b %d, %Y")

    def get_reading_time_display(self) -> str:
        """Get formatted string for total reading time."""
        if self.total_reading_time_hours is None:
            return "— hours"
        if self.total_reading_time_hours < 1:
            minutes = int(self.total_reading_time_hours * 60)
            return f"{minutes} minutes"
        return f"{self.total_reading_time_hours:.1f} hours"

    def get_days_reading_display(self) -> str:
        """Get formatted string for days spent reading."""
        if self.days_reading is None:
            return "— days"
        return f"{self.days_reading} days"

import dataclasses

import dataclasses_json
from dataclasses_json.api import DataClassJsonMixin


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class ReadBookStatistics(DataClassJsonMixin):
    book_id: int  # the ID of this book in our library
    begin_time: float # the time the user began reading the book
    finish_time: float # the time the user finished reading the book

@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class LendBookStatistics(DataClassJsonMixin):
    book_id: int  # the ID of this book in our library
    begin_time: float # the time the user began reading the book
    finish_time: float # the time the user finished reading the book

@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class BookIdStatistics(DataClassJsonMixin):
    book_id: int  # the ID of this book in our library

@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Statistics(DataClassJsonMixin):
    book_reading_sessions: list[ReadBookStatistics]
    book_lending_sessions: list[LendBookStatistics]
    books_dismissed: list[BookIdStatistics]
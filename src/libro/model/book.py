import dataclasses
from enum import StrEnum, auto
from typing import Optional

import dataclasses_json

from ..storage.storable import StorableObject


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Author:
    first_name: str
    last_name: str
    biograpohy: Optional[str] = None

    def full_name(self) -> str:
        return self.first_name + " " + self.last_name


class Genre(StrEnum):
    Fiction = auto()
    Nonfiction = auto()
    Scifi = auto()
    Mystery = auto()
    Biography = auto()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Book(StorableObject):
    title: str
    author: Author
    genre: Genre
    pages: int
    publish_year: int
    summary: Optional[str] = None
    cover: Optional[str] = None
    current_page: int | None = None


@dataclasses.dataclass(frozen=True)
class BookFilter:
    query: str
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    pages_min: Optional[int] = None
    pages_max: Optional[int] = None
    genre: Optional[str] = None

    # should the query be checked against any of the following?
    include_title: bool = True
    include_author: bool = True
    include_summary: bool = True

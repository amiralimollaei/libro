import dataclasses
from enum import StrEnum, auto
from typing import Optional

import dataclasses_json
from dataclasses_json.api import DataClassJsonMixin


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Author:
    first_name: str
    last_name: str
    biograpohy: Optional[str] = None

    def full_name(self):
        return self.first_name + " " + self.last_name


class Genre(StrEnum):
    Fiction = auto()
    Nonfiction = auto()
    Scifi = auto()
    Mystery = auto()
    Biography = auto()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Book(DataClassJsonMixin):
    title: str
    author: Author
    genre: Genre
    pages: int
    publish_year: int
    summary: Optional[str] = None
    cover: Optional[str] = None
    id: int | None = None

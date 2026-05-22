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
    summary: Optional[str] = None

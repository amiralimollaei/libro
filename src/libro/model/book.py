import dataclasses
from enum import StrEnum, auto
import re
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
    # General
    Fiction = auto()
    Nonfiction = auto()

    # Fiction
    Fantasy = auto()
    HighFantasy = auto()
    UrbanFantasy = auto()
    DarkFantasy = auto()
    SwordAndSorcery = auto()

    Scifi = auto()
    HardScifi = auto()
    SoftScifi = auto()
    SpaceOpera = auto()
    Cyberpunk = auto()
    Steampunk = auto()
    Dystopian = auto()
    Utopian = auto()
    PostApocalyptic = auto()
    AlternateHistory = auto()
    TimeTravel = auto()

    Mystery = auto()
    CozyMystery = auto()
    Detective = auto()
    Crime = auto()
    Noir = auto()
    Thriller = auto()
    PsychologicalThriller = auto()
    LegalThriller = auto()
    PoliticalThriller = auto()
    SpyThriller = auto()

    Horror = auto()
    GothicHorror = auto()
    SupernaturalHorror = auto()
    CosmicHorror = auto()

    Adventure = auto()
    Action = auto()
    Survival = auto()
    Western = auto()

    Romance = auto()
    HistoricalRomance = auto()
    ParanormalRomance = auto()
    RomanticComedy = auto()

    HistoricalFiction = auto()
    LiteraryFiction = auto()
    ContemporaryFiction = auto()
    FamilySaga = auto()

    Drama = auto()
    Humor = auto()
    Satire = auto()
    Comedy = auto()
    Tragedy = auto()

    YoungAdult = auto()
    NewAdult = auto()
    ComingOfAge = auto()

    MagicalRealism = auto()
    FairyTale = auto()
    Mythology = auto()
    Folklore = auto()

    WarFiction = auto()
    MilitaryFiction = auto()

    ShortStories = auto()
    Anthology = auto()

    # Nonfiction
    Biography = auto()
    Autobiography = auto()
    Memoir = auto()

    History = auto()
    MilitaryHistory = auto()
    WorldHistory = auto()

    Science = auto()
    Physics = auto()
    Astronomy = auto()
    Biology = auto()
    Chemistry = auto()
    Mathematics = auto()
    ComputerScience = auto()

    Technology = auto()
    Programming = auto()
    Engineering = auto()

    Philosophy = auto()
    Psychology = auto()
    Sociology = auto()
    Anthropology = auto()

    Politics = auto()
    Economics = auto()
    Business = auto()
    Finance = auto()

    SelfHelp = auto()
    PersonalDevelopment = auto()
    Productivity = auto()

    Health = auto()
    Fitness = auto()
    Nutrition = auto()

    Religion = auto()
    Spirituality = auto()

    Education = auto()
    Language = auto()

    Travel = auto()
    Nature = auto()

    Art = auto()
    Music = auto()
    Photography = auto()

    Cooking = auto()
    Crafts = auto()
    Hobbies = auto()

    Reference = auto()
    Encyclopedia = auto()
    Textbook = auto()
    Academic = auto()

    Essays = auto()
    Journalism = auto()
    TrueCrime = auto()

    # Children's
    Childrens = auto()
    PictureBook = auto()
    MiddleGrade = auto()
    
    @property
    def label(self) -> str:
        return re.sub(r'(?<!^)([A-Z])', r' \1', self.name)


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

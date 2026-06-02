import dataclasses
from typing import Optional

import dataclasses_json


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Person:
    first_name: str
    last_name: str
    biograpohy: Optional[str] = None

    def full_name(self) -> str:
        return self.first_name + " " + self.last_name
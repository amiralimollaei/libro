import dataclasses
from typing import Optional

import dataclasses_json


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Person:
    name: str
    biograpohy: Optional[str] = None

    def full_name(self) -> str:
        return self.name

import dataclasses

import dataclasses_json
from dataclasses_json.api import DataClassJsonMixin


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class Todo(DataClassJsonMixin):
    id: int
    time: float

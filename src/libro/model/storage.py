import dataclasses

import dataclasses_json

from ..storage.storable import StorableObject


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class IdNumeralStorageMeta(StorableObject):
    class_name: str
    last_id: int
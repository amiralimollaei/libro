import dataclasses
import time
from datetime import datetime
from typing import Optional

import dataclasses_json

from ..model.person import Person
from ..storage.json import StorableObject


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class LendingEntry(StorableObject):
    book_id: int
    borrower: Person
    lent_date: float
    due_date: float
    returned_time: Optional[float] = None
    note: Optional[str] = None

    @property
    def is_returned(self) -> bool:
        return self.returned_time is not None

    @property
    def is_overdue(self) -> bool:
        return (
            self.returned_time is None
            and self.due_date < time.time()
        )

    @property
    def due_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.due_date)

    @property
    def lent_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.lent_date)
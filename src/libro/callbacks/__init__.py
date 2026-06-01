from dataclasses import dataclass
from typing import Any


class CallbackContext:
    """
    Base class for all CallbackContexts.

    `CallbackContext` stores the callback's identifier, whether or not the callback is cancelled, 
    the result of the callback, and the information that is passed to the callback funtion.
    """

    id: str

    def __init__(self):
        self.result = None
        self._is_cancelled = False

    def get_callback_id(self) -> str:
        return self.id

    def get_id(self) -> str:
        return self.id

    def cancel(self):
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, is_cancelled={self._is_cancelled}, ...)"


@dataclass
class CallbackResult:
    result: Any
    is_cancelled: bool = False


class CallbackMixin:
    """
    Implements Callbacks as a Mixin for a class, callback functions are given a `CallbackContext` and
    should modify the callback context's result in place to return a value
    """

    def __init_callbacks__(self, callback_ids: list):
        self.__callbacks__: dict[str, list] = {}
        for id in callback_ids:
            self.__callbacks__.update({id: []})

    def validate_callback_id(self, callback_id):
        if callback_id not in self.__callbacks__.keys():
            raise ValueError(
                f"Callback with id=\"{callback_id}\" does not exist, available: {list(self.__callbacks__.keys())}."
            )

    def register_callback(self, calllback_id: str, fn):
        self.validate_callback_id(calllback_id)
        self.__callbacks__[calllback_id].append(fn)

    def list_available_callbacks(self):
        return list(self.__callbacks__.keys())

    def _run_callbacks(self, context: CallbackContext) -> CallbackResult:
        if context.is_cancelled():
            return CallbackResult(context.result, is_cancelled=True)

        callback_id = context.get_callback_id()
        self.validate_callback_id(callback_id)

        for fn in self.__callbacks__[callback_id]:
            fn(context)  # function modifies context in-place
            if context.is_cancelled():
                return CallbackResult(context.result, is_cancelled=True)

        return CallbackResult(context.result)

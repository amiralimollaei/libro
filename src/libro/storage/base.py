from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Generic, Self, Type, TypeVar, cast

from dataclasses_json import DataClassJsonMixin

from ..callbacks import CallbackContext, CallbackMixin, CallbackResult


class StorableObject(DataClassJsonMixin):
    """
    Base class for all of Libro's storable Objects
    """

    ...


T = TypeVar("T", bound="StorableObject")


class OnObjectAddCtx(Generic[T], CallbackContext):
    id = "on_object_add"

    def __init__(self, obj: T):
        super().__init__()

        self.obj: T = obj


class OnObjectRemoveCtx(Generic[T], CallbackContext):
    id = "on_object_remove"

    def __init__(self, obj: T):
        super().__init__()

        self.obj: T = obj


class OnObjectsChangedCtx(CallbackContext):
    id = "on_objects_changed"

    def __init__(self):
        super().__init__()


class StorageHandler(Generic[T], ABC, CallbackMixin):
    def __init__(self):
        self.__init_callbacks__([
            OnObjectAddCtx.id,
            OnObjectRemoveCtx.id,
            OnObjectsChangedCtx.id
        ])

    def _notify_changed(self) -> CallbackResult:
        return self._run_callbacks(OnObjectsChangedCtx())

    def _notify_add(self, obj: T) -> CallbackResult:
        return self._run_callbacks(OnObjectAddCtx[T](obj))

    def _notify_remove(self, obj: T) -> CallbackResult:
        return self._run_callbacks(OnObjectRemoveCtx[T](obj))

    def register_add_callback(self, fn: Callable[[OnObjectAddCtx[T]], None]):
        self.register_callback(OnObjectAddCtx.id, fn=fn)

    def register_remove_callback(self, fn: Callable[[OnObjectRemoveCtx[T]], None]):
        self.register_callback(OnObjectRemoveCtx.id, fn=fn)

    def register_change_callback(self, fn: Callable[[OnObjectsChangedCtx], None]):
        self.register_callback(OnObjectsChangedCtx.id, fn=fn)

    @classmethod
    @abstractmethod
    def from_path(cls, item_cls: Type[T], path: Path) -> Self:
        ...
    
    @abstractmethod
    def save(self) -> None:
        ...


S = TypeVar("S", bound=StorageHandler)
StorageKey = tuple[type[StorageHandler], type[StorableObject]]


class LibroStorage:
    """
    Holds all storage handlers globally.
    """

    _storages: dict[StorageKey, StorageHandler] = {}

    @staticmethod
    def register(
        storage_cls: type[S],
        item_cls: type[T],
        storage: S,
    ) -> None:
        key = (storage_cls, item_cls)

        if key in LibroStorage._storages:
            raise ValueError(
                f"Storage already registered for "
                f"{storage_cls.__name__}[{item_cls.__name__}]"
            )

        LibroStorage._storages[key] = storage

    @staticmethod
    def new(
        storage_cls: type[S],
        item_cls: type[T],
        path: Path,
    ) -> S:
        key = (storage_cls, item_cls)

        if key in LibroStorage._storages:
            raise ValueError(
                f"Storage already registered for "
                f"{storage_cls.__name__}[{item_cls.__name__}]"
            )

        LibroStorage._storages[key] = storage_cls.from_path(item_cls=item_cls, path=path)
        return cast(S, LibroStorage._storages[key])

    @staticmethod
    def get(
        storage_cls: type[S],
        item_cls: type[T],
    ) -> S:
        key = (storage_cls, item_cls)

        try:
            return cast(S, LibroStorage._storages[key])
        except KeyError:
            raise KeyError(
                f"No storage registered for "
                f"{storage_cls.__name__}[{item_cls.__name__}]"
            )

    def save_all(self):
        for storage in LibroStorage._storages.values():
            storage.save()
import hashlib
import os
from pathlib import Path
from typing import Any, Callable, Generic, Optional, Type, TypeVar

from dataclasses_json.api import DataClassJsonMixin

from ..callbacks import CallbackMixin, CallbackContext


T = TypeVar("T", bound="DataClassJsonMixin")


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


class OnObjectsChangedCtx(Generic[T], CallbackContext):
    id = "on_objects_changed"

    def __init__(self, objects: list[T]):
        super().__init__()

        self.objects: list[T] = objects


class JsonDirectoryStorage(Generic[T], CallbackMixin):
    def __init__(self, directory: Path, objects: Optional[list[T]] = None) -> None:
        directory.mkdir(exist_ok=True)

        self.directory = directory

        self.objects: list[T] = objects or []

        self.__init_callbacks__([
            OnObjectAddCtx.id,
            OnObjectRemoveCtx.id,
            OnObjectsChangedCtx.id
        ])

    def register_add_callback(self, fn: Callable[[OnObjectAddCtx[T]], None]):
        self.register_callback(OnObjectAddCtx.id, fn=fn)

    def register_remove_callback(self, fn: Callable[[OnObjectRemoveCtx[T]], None]):
        self.register_callback(OnObjectRemoveCtx.id, fn=fn)

    def register_change_callback(self, fn: Callable[[OnObjectsChangedCtx[T]], None]):
        self.register_callback(OnObjectsChangedCtx.id, fn=fn)

    def add(self, obj: T):
        ctx = self._run_callbacks(OnObjectAddCtx[T](obj))
        if not ctx.is_cancelled:
            self.objects.append(obj)
            self._run_callbacks(OnObjectsChangedCtx[T](self.objects))

    def remove(self, obj: T):
        ctx = self._run_callbacks(OnObjectRemoveCtx[T](obj))
        if not ctx.is_cancelled:
            self.objects.remove(obj)
            json_data = obj.to_json().encode("utf-8")
            hash = hashlib.sha256(json_data)
            filename = self.directory / f"{hash.hexdigest()}.json"
            os.remove(filename)
            self._run_callbacks(OnObjectsChangedCtx[T](self.objects))

    def save(self):
        for obj in self.objects:
            json_data = obj.to_json().encode("utf-8")
            hash = hashlib.sha256(json_data)
            filename = self.directory / f"{hash.hexdigest()}.json"
            if not filename.exists():
                open(filename, mode="wb").write(json_data)

    @classmethod
    def from_directory(cls, item_cls: Type[T], directory: Path) -> JsonDirectoryStorage[T]:
        objects: list[T] = []

        if not directory.exists():
            return cls(directory)

        for filename in directory.glob("*.json"):
            with open(filename, mode="r", encoding="utf-8") as f:
                obj = item_cls.from_json(f.read())
                objects.append(obj)

        return cls(directory, objects=objects)


class JsonFileStorage(Generic[T]):
    def __init__(self, path: Path, object: Optional[T] = None) -> None:
        path.parent.mkdir(exist_ok=True)

        self.path = path

        self.object: Optional[T] = object

    def get(self) -> Optional[T]:
        return self.object

    def update(self, obj: T):
        self.object = obj

    def save(self):
        assert self.object is not None
        json_data = self.object.to_json().encode("utf-8")
        if not self.path.exists():
            open(self.path, mode="wb").write(json_data)

    @classmethod
    def from_directory(cls, item_cls: Type[T], path: Path) -> JsonFileStorage[T]:
        object: Optional[T] = None

        if not path.exists():
            return cls(path, object)

        with open(path, mode="r", encoding="utf-8") as f:
            object = item_cls.from_json(f.read())

        return cls(path, object)

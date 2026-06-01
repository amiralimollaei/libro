import hashlib
import os
from pathlib import Path
from typing import Any, Callable, Generic, Optional, Type, TypeVar

from dataclasses_json.api import DataClassJsonMixin


T = TypeVar("T", bound="DataClassJsonMixin")


class JsonDirectoryStorage(Generic[T]):
    def __init__(self, directory: Path, objects: Optional[list[T]] = None) -> None:
        super().__init__()
        directory.mkdir(exist_ok=True)

        self.directory = directory

        self.objects: list[T] = objects or []

        self.on_add_callback_fn: Optional[Callable[[T], Any]] = None
        self.on_remove_callback_fn: Optional[Callable[[T], Any]] = None

    def register_add_callback(self, fn: Callable[[T], Any]):
        self.on_add_callback_fn = fn
    
    def register_remove_callback(self, fn: Callable[[T], Any]):
        self.on_remove_callback_fn = fn
    
    def add(self, obj: T):
        self.objects.append(obj)

    def remove(self, obj: T):
        self.objects.remove(obj)
        json_data = obj.to_json().encode("utf-8")
        hash = hashlib.sha256(json_data)
        filename = self.directory / f"{hash.hexdigest()}.json"
        os.remove(filename)

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
        super().__init__()
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

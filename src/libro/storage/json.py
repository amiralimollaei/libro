import dataclasses
import hashlib
import os
from pathlib import Path
from typing import Callable, Optional, Self, Type

import dataclasses_json

from .base import T, StorableObject, StorageHandler


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)  # pyright: ignore[reportArgumentType]
@dataclasses.dataclass
class IdNumeralStorageMeta(StorableObject):
    class_name: str
    last_id: int


class JsonBlobStorage(StorageHandler[T]):
    def __init__(self, directory: Path, objects: Optional[list[T]] = None) -> None:
        super().__init__()
        directory.mkdir(parents=True, exist_ok=True)

        self.directory = directory

        self.objects: list[T] = objects or []

    def add(self, obj: T):
        if not self._notify_add(obj).is_cancelled:
            self.objects.append(obj)
            self._notify_changed()

    def remove(self, obj: T):
        if not self._notify_remove(obj).is_cancelled:
            self.objects.remove(obj)
            json_data = obj.to_json().encode("utf-8")
            hash = hashlib.sha256(json_data)
            filename = self.directory / f"{hash.hexdigest()}.json"
            os.remove(filename)
            self._notify_changed()

    def save(self):
        for obj in self.objects:
            json_data = obj.to_json().encode("utf-8")
            hash = hashlib.sha256(json_data)
            path = self.directory / f"{hash.hexdigest()}.json"
            path.write_bytes(json_data)

    @classmethod
    def from_path(cls, item_cls: Type[T], path: Path) -> Self:
        objects: list[T] = []

        if not path.exists():
            return cls(path)

        for _path in path.glob("*.json"):
            obj = item_cls.from_json(_path.read_bytes())
            objects.append(obj)

        return cls(path, objects=objects)


class JsonIdNumeralStorage(StorageHandler[T]):
    META_FILE = "storage.json"

    def __init__(self, directory: Path, objects: Optional[dict[int, T]] = None, meta: Optional[IdNumeralStorageMeta] = None) -> None:
        super().__init__()
        directory.mkdir(parents=True, exist_ok=True)

        self.directory = directory

        self.objects: dict[int, T] = objects or dict()
        self.meta = meta or IdNumeralStorageMeta(
            class_name=self.__class__.__name__,
            last_id=0
        )
        self.meta_path = self.directory / self.META_FILE

    def add(self, obj: T) -> int:
        if not self._notify_add(obj).is_cancelled:
            self.meta.last_id += 1
            self.objects[self.meta.last_id] = obj
            self._notify_changed()
        return self.meta.last_id

    def remove_by_id(self, id: int):
        if not self._notify_remove(self.objects[id]).is_cancelled:
            del self.objects[id]
            os.remove(self.directory / f"{id}.json")
            self._notify_changed()

    def update_by_id(self, id: int, obj: T):
        self.objects[id] = obj
        self._notify_changed()
        self._save_object(id, obj)

    def get(self, id: int) -> Optional[T]:
        return self.objects[id] if id in self.objects.keys() else None

    def get_or_default(self, id: int, default: T) -> T:
        if id not in self.objects.keys():
            self.objects[id] = default
        return self.objects[id]

    def compute_if_absent(self, id: int, fn: Callable[[], T]) -> T:
        if id not in self.objects.keys():
            self.objects[id] = fn()
        return self.objects[id]

    def _save_object(self, id: int, obj: T):
        json_data = obj.to_json().encode("utf-8")
        path = self.directory / f"{id}.json"
        path.write_bytes(json_data)

    def save(self):
        for id, obj in self.objects.items():
            self._save_object(id, obj)
        self.meta_path.write_bytes(self.meta.to_json().encode("utf-8"))

    @classmethod
    def from_path(cls, item_cls: Type[T], path: Path) -> Self:
        objects: dict[int, T] = dict()

        if not path.exists():
            return cls(path)

        meta_path = path / cls.META_FILE
        if meta_path.exists():
            meta = IdNumeralStorageMeta.from_json(meta_path.read_bytes())
        else:
            return cls(path)
        # assert meta.class_name == cls.__class__.__name__

        for _path in path.glob("*.json"):
            if _path.name == cls.META_FILE:
                continue
            try:
                id = int(_path.name.split(".")[0])
            except Exception:
                continue
            objects[id] = item_cls.from_json(_path.read_bytes())

        return cls(path, objects=objects, meta=meta)


class JsonFileStorage(StorageHandler[T]):
    def __init__(self, path: Path, object: Optional[T] = None) -> None:
        super().__init__()
        path.parent.mkdir(parents=True, exist_ok=True)

        self.path = path

        self.object: Optional[T] = object

    def get(self) -> Optional[T]:
        return self.object

    def update(self, obj: T):
        self.object = obj
        self._notify_changed()

    def save(self):
        assert self.object is not None
        json_data = self.object.to_json().encode("utf-8")
        self.path.write_bytes(json_data)

    @classmethod
    def from_path(cls, item_cls: Type[T], path: Path) -> Self:
        object: Optional[T] = None

        if not path.exists():
            return cls(path, object)

        object = item_cls.from_json(path.read_bytes())

        return cls(path, object)

from abc import ABC, abstractmethod
import hashlib
import json
from pathlib import Path
from typing import Generic, Optional, Type, TypeVar

from dataclasses_json.api import DataClassJsonMixin


T = TypeVar("T", bound="DataClassJsonMixin")


class JsonObjectStorage(Generic[T]):
    def __init__(self, directory: Path, objects: Optional[list[T]] = None) -> None:
        super().__init__()
        directory.mkdir(exist_ok=True)

        self.directory = directory

        self.objects: list[T] = objects or []

    def add(self, obj: T):
        self.objects.append(obj)

    def remove(self, obj: T):
        self.objects.remove(obj)

    def save(self):
        for obj in self.objects:
            json_data = obj.to_json().encode("utf-8")
            hash = hashlib.sha256(json_data)
            filename = self.directory / f"{hash.hexdigest()}.json"
            open(filename, mode="wb").write(json_data)

    @classmethod
    def from_directory(cls, item_cls: Type[T], directory: Path) -> "JsonObjectStorage[T]":
        objects: list[T] = []

        if not directory.exists():
            return cls(directory)

        for filename in directory.glob("*.json"):
            with open(filename, mode="r", encoding="utf-8") as f:
                obj = item_cls.from_json(f.read())
                objects.append(obj)

        return cls(directory, objects=objects)

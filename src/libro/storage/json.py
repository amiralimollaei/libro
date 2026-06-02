import hashlib
import os
from pathlib import Path
from typing import Callable, Generic, Optional, Type, TypeVar

from libro.model.storage import IdNumeralStorageMeta

from ..storage.storable import StorableObject
from ..callbacks import CallbackMixin, CallbackContext, CallbackResult


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


class StorageBase(Generic[T], CallbackMixin):
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


class JsonBlobStorage(StorageBase[T]):
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
    def from_directory(cls, item_cls: Type[T], directory: Path) -> JsonBlobStorage[T]:
        objects: list[T] = []

        if not directory.exists():
            return cls(directory)

        for path in directory.glob("*.json"):
            obj = item_cls.from_json(path.read_bytes())
            objects.append(obj)

        return cls(directory, objects=objects)


class JsonIdNumeralStorage(StorageBase[T]):
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
        self._save_object(id, obj)
        self._notify_changed()

    def get(self, id: int) -> Optional[T]:
        return self.objects[id] if id in self.objects.keys() else None

    def get_or_default(self, id: int, default: T) -> T:
        return self.objects[id] if id in self.objects.keys() else default

    def compute_if_absent(self, id: int, fn: Callable[[], T]) -> T:
        return self.objects[id] if id in self.objects.keys() else fn()

    def _save_object(self, id: int, obj: T):
        json_data = obj.to_json().encode("utf-8")
        path = self.directory / f"{id}.json"
        path.write_bytes(json_data)

    def save(self):
        for id, obj in self.objects.items():
            self._save_object(id, obj)
        self.meta_path.write_bytes(self.meta.to_json().encode("utf-8"))

    @classmethod
    def from_directory(cls, item_cls: Type[T], directory: Path) -> JsonIdNumeralStorage[T]:
        objects: dict[int, T] = dict()

        if not directory.exists():
            return cls(directory)

        meta_path = directory / cls.META_FILE
        if meta_path.exists():
            meta = IdNumeralStorageMeta.from_json(meta_path.read_bytes())
        else:
            return cls(directory)
        # assert meta.class_name == cls.__class__.__name__

        for path in directory.glob("*.json"):
            if path.name == cls.META_FILE:
                continue
            try:
                id = int(path.name.split(".")[0])
            except Exception:
                continue
            objects[id] = item_cls.from_json(path.read_bytes())

        return cls(directory, objects=objects, meta=meta)


class JsonFileStorage(Generic[T]):
    def __init__(self, path: Path, object: Optional[T] = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        self.path = path

        self.object: Optional[T] = object

    def get(self) -> Optional[T]:
        return self.object

    def update(self, obj: T):
        self.object = obj

    def save(self):
        assert self.object is not None
        json_data = self.object.to_json().encode("utf-8")
        self.path.write_bytes(json_data)

    @classmethod
    def from_directory(cls, item_cls: Type[T], path: Path) -> JsonFileStorage[T]:
        object: Optional[T] = None

        if not path.exists():
            return cls(path, object)

        object = item_cls.from_json(path.read_bytes())

        return cls(path, object)

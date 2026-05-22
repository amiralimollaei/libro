import os
from pathlib import Path
from typing import Sequence


class LibroPaths:
    _root = Path("~/.libro")

    # ---- configuration ----
    @classmethod
    def set_root(cls, root: str | Path) -> None:
        cls._root = Path(root)

    @classmethod
    def root(cls) -> Path:
        return cls._root.expanduser()

    # ---- paths ----
    @classmethod
    def books(cls) -> Path:
        """Contains data for every books in our library"""
        return cls.root() / "books"

    @classmethod
    def covers(cls) -> Path:
        """Contains book cover images for books in our library"""
        return cls.root() / "covers"

    @classmethod
    def assets(cls) -> Path:
        """Contains Libro internal assets"""
        return cls.root() / "assets"


def clean_dict(d: dict):
    final_dict = {}
    for k, v in d.items():
        if v is None:
            continue
        elif isinstance(v, dict):
            if len(v) == 0:
                continue
            v = clean_dict(v)
        elif isinstance(v, Sequence):
            if len(v) == 0:
                continue
            # Other than strings, every other sequence is assumed to be a nested dynamic type
            if not isinstance(v, str):
                v = [(clean_dict(e) if isinstance(e, dict) else e) for e in v]
        final_dict[k] = v
    return final_dict


if __package__ is not None:
    import importlib.resources
    import shutil

    MODULE_PATH = importlib.resources.files(__package__)
    RESOURCES_PATH = str(MODULE_PATH / "assets")

    # If the LibroPaths.RESOURCES folder doesn't exist, We should copy all our default assets
    def copy_if_absent(src: str, dst: str, *, follow_symlinks: bool = True):
        if os.path.exists(dst):
            if os.path.isdir(dst):
                raise FileExistsError(f"directory exists with the same name as destination the file: {dst}")
            return
        shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

    def copy_default_resources():
        os.makedirs(LibroPaths.assets(), exist_ok=True)
        shutil.copytree(RESOURCES_PATH, LibroPaths.assets(), dirs_exist_ok=True, copy_function=copy_if_absent)

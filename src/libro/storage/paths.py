import os
from pathlib import Path
from typing import Sequence


def find_data_directory():
    app_data_dir = os.getenv("FLET_APP_STORAGE_DATA")
    if app_data_dir:
        return Path(app_data_dir) / ".libro"
    else:
        return Path.home() / ".libro"


class LibroPaths:
    _root = find_data_directory()

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
    def lending(cls) -> Path:
        """Contains data related to the lending tab"""
        return cls.root() / "lending"

    @classmethod
    def covers(cls) -> Path:
        """Contains book cover images for books in our library"""
        return cls.root() / "covers"

    @classmethod
    def assets(cls) -> Path:
        """Contains Libro internal assets"""
        return cls.root() / "assets"

    @classmethod
    def book_index(cls) -> Path:
        """Contains Libro internal index for the book search engine"""
        return cls.books() / "index"

    @classmethod
    def statistics(cls) -> Path:
        """Contains the statistics object"""
        return cls.root() / "statistics.json"


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

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BookContext:
    pk: int
    uuid: str
    folder_path: str


@dataclass
class SubfolderContext:
    name: str
    path: str
    book_start_page: int | None

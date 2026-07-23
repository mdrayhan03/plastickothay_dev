"""Cursor pagination primitives.

Cursors are opaque strings to the domain; the repository adapter encodes and decodes them
(LLD §8.4 — cursor over ``(created DESC, id DESC)``).
"""

from dataclasses import dataclass, field

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class PageRequest:
    limit: int = DEFAULT_PAGE_SIZE
    cursor: str | None = None

    def __post_init__(self) -> None:
        if self.limit < 1:
            object.__setattr__(self, "limit", DEFAULT_PAGE_SIZE)
        elif self.limit > MAX_PAGE_SIZE:
            object.__setattr__(self, "limit", MAX_PAGE_SIZE)


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T] = field(default_factory=list)
    next_cursor: str | None = None

    @property
    def has_next(self) -> bool:
        return self.next_cursor is not None

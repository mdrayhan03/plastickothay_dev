"""Transaction boundary port.

``transaction.atomic()`` is a Django import and cannot appear in core/ (LLD §2.1), but use
cases still need to declare all-or-nothing boundaries. They say what must commit together;
the persistence adapter decides how.

    with self.uow:
        self.images.upload(...)
        self.posts.add(post)
        self.uow.commit()

Leaving the block without ``commit()`` rolls back.
"""

from abc import ABC, abstractmethod
from types import TracebackType


class UnitOfWork(ABC):
    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

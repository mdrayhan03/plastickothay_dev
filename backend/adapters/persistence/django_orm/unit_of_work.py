"""Django transaction adapter for the UnitOfWork port.

This is the one place transaction.atomic() lives on the write path — the reason the port
exists is to keep that Django import out of core/ while still letting use cases declare
all-or-nothing boundaries (LLD §6).

Implementation note: atomic() is entered lazily on __enter__ and committed by leaving the
block cleanly; an exception (or a missing commit()) triggers atomic()'s own rollback. commit()
is a marker that the work should stand — the actual COMMIT is Django's on block exit.
"""

from types import TracebackType

from django.db import transaction

from core.ports.unit_of_work import UnitOfWork


class DjangoUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._atomic: transaction.Atomic | None = None
        self._committed = False

    def __enter__(self) -> "DjangoUnitOfWork":
        self._atomic = transaction.atomic()
        self._atomic.__enter__()
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._atomic is not None
        # If the caller never marked the work committed, force a rollback even on a clean
        # exit by raising inside the atomic block via set_rollback.
        if exc_type is None and not self._committed:
            transaction.set_rollback(True)
        self._atomic.__exit__(exc_type, exc, tb)
        self._atomic = None

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        transaction.set_rollback(True)

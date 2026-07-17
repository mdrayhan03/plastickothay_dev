"""Admin-editable contact page (singleton).

Structured fields rather than one JSON blob: Postgres would happily store a blob, but then
nothing validates it and every consumer re-derives the shape. Since this is an admin form,
validation belongs server-side (LLD §3 answer).
"""

from dataclasses import dataclass

from core.domain.entities import ContactPage
from core.domain.ids import UserId
from core.domain.value_objects import GeoPoint, SocialLink
from core.ports.clock import Clock
from core.ports.repositories import ContactRepository
from core.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class UpdateContactPageCommand:
    heading: str
    intro: str
    email: str
    phone: str
    address: str
    map_lat: float | None = None
    map_lon: float | None = None
    socials: tuple[SocialLink, ...] = ()


class GetContactPage:
    def __init__(self, contact: ContactRepository) -> None:
        self.contact = contact

    def execute(self) -> ContactPage:
        return self.contact.get_page()


class UpdateContactPage:
    def __init__(self, contact: ContactRepository, uow: UnitOfWork, clock: Clock) -> None:
        self.contact = contact
        self.uow = uow
        self.clock = clock

    def execute(self, cmd: UpdateContactPageCommand, actor_id: UserId) -> ContactPage:
        map_point = None
        if cmd.map_lat is not None and cmd.map_lon is not None:
            map_point = GeoPoint(cmd.map_lat, cmd.map_lon)  # validates range

        with self.uow:
            page = ContactPage(
                heading=cmd.heading.strip(),
                intro=cmd.intro.strip(),
                email=cmd.email.strip(),
                phone=cmd.phone.strip(),
                address=cmd.address.strip(),
                map_point=map_point,
                socials=list(cmd.socials),
                updated_at=self.clock.now(),
                updated_by=actor_id,
            )
            saved = self.contact.save_page(page)
            self.uow.commit()
        return saved

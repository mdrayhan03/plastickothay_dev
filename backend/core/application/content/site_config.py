"""Site configuration use cases — admin-editable application settings."""

from dataclasses import dataclass, field

from core.domain.entities import SiteConfig
from core.domain.ids import UserId
from core.domain.value_objects import GeoPoint, ImageRef, WeekStart
from core.ports.clock import Clock
from core.ports.repositories import SiteConfigRepository
from core.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class UpdateSiteConfigCommand:
    week_start: str
    site_name: str
    tagline: str = ""
    map_lat: float | None = None
    map_lon: float | None = None
    map_zoom: int = 12
    logo: ImageRef | None = None  # set by the logo-upload flow; None leaves it unchanged
    flags: dict[str, bool] = field(default_factory=dict)


class GetSiteConfig:
    def __init__(self, config: SiteConfigRepository) -> None:
        self.config = config

    def execute(self) -> SiteConfig:
        return self.config.get()


class UpdateSiteConfig:
    def __init__(self, config: SiteConfigRepository, uow: UnitOfWork, clock: Clock) -> None:
        self.config = config
        self.uow = uow
        self.clock = clock

    def execute(self, cmd: UpdateSiteConfigCommand, actor_id: UserId) -> SiteConfig:
        map_center = None
        if cmd.map_lat is not None and cmd.map_lon is not None:
            map_center = GeoPoint(cmd.map_lat, cmd.map_lon)  # validates range

        current = self.config.get()
        with self.uow:
            updated = SiteConfig(
                week_start=WeekStart(cmd.week_start),
                site_name=cmd.site_name.strip() or "PlasticKothay",
                tagline=cmd.tagline.strip(),
                logo=cmd.logo if cmd.logo is not None else current.logo,
                map_center=map_center,
                map_zoom=cmd.map_zoom,
                flags=dict(cmd.flags),
                updated_at=self.clock.now(),
                updated_by=actor_id,
            )
            saved = self.config.save(updated)
            self.uow.commit()
        return saved

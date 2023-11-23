from dataclasses import dataclass, field
from typing import Union

from dynaconf import settings


@dataclass
class AppSettings:
    env: str | None = field(default=settings.ENV)
    container_env: bool | None = field(default=settings.CONTAINER_ENV)
    log_level: str | None = field(default=settings.LOG_LEVEL)

    def __post_init__(self):
        self.log_level: str = str(settings.LOG_LEVEL).upper()

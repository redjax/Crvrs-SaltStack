from loguru import logger as log
from dataclasses import dataclass, field

from dynaconf import settings

SALT_MASTER_ADDRESS: str = settings.SALT_MASTER.HOST


@dataclass
class SaltMaster:
    name: str | None = field(default=settings.SALT_MASTER.NAME)
    host: str | None = field(default=SALT_MASTER_ADDRESS)
    os_type: str | None = field(default=settings.SALT_MASTER.OS_TYPE)
    linux_distro: str | None = field(default=settings.SALT_MASTER.LINUX_DISTRO)


@dataclass
class SaltMinion:
    name: str | None = field(default=None)
    master_addr: str | None = field(default=SALT_MASTER_ADDRESS)
    host: str | None = field(default=None)
    os_type: str | None = field(default=None)
    linux_distro: str | None = field(default=None)


SALT_MASTER: SaltMaster = SaltMaster()

env_minions: list[dict[str, str]] = settings.SALT_MINIONS

SALT_MINIONS: list[SaltMinion] = []

for minion in env_minions:
    _minion: SaltMinion = SaltMinion(
        name=minion.name,
        host=minion.host,
        os_type=minion.os_type,
        linux_distro=minion.linux_distro,
    )
    SALT_MINIONS.append(_minion)

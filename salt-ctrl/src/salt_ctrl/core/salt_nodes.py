from __future__ import annotations

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from pathlib import Path
from typing import Union

from salt_ctrl.domain.inventory import SaltInventory, SaltMaster, SaltMinion

from loguru import logger as log

inventory = SaltInventory()
inventory.load_all()

SALT_MASTER: SaltMaster = inventory.master
SALT_MINIONS: list[SaltMinion] = inventory.minions
SALT_MASTER_ADDRESS: str = inventory.master.host

if __name__ == "__main__":
    log.debug(f"Master: {inventory.master}")
    log.debug(f"Minions ({inventory.count_minions}): {inventory.minions}")

    log.info(
        f"Master node [{inventory.master.name}] reachable: {inventory.master.reachable()}"
    )

    for minion in inventory.minions:
        log.info(f"Minion [{minion.name}] reachable: {minion.reachable()}")

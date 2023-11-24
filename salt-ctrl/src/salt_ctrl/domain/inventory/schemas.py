import json
from typing import Union
from pathlib import Path

from loguru import logger as log
from pydantic import BaseModel, Field, field_validator, ValidationError

from salt_ctrl.constants import INVENTORY_DIR
from salt_ctrl.utils.net_utils import ping

from red_utils.ext.context_managers.cli_spinners import SimpleSpinner


class SaltInventoryBase(BaseModel):
    inventory_dir: Path = Field(default=INVENTORY_DIR)
    master: "SaltMaster" = Field(default=None)
    minions: list["SaltMinion"] = Field(default=None)

    @property
    def master_file(self) -> Path:
        return Path(f"{self.inventory_dir}/master.json")

    @property
    def minions_file(self) -> Path:
        return Path(f"{self.inventory_dir}/minions.json")

    def load_all(self) -> bool:
        log.info(f"Populating Salt inventory.")
        _master: bool = self.load_master()
        _minions: bool = self.load_minions()

        if _master and _minions:
            return True
        elif not _master and not _minions:
            log.error(f"Failed loading both Salt minions and master.")

            return False
        else:
            log.error(
                f"Load minions success: [{_minions}]\n\tLoad master succes: [{_master}]"
            )

            return False

    def load_master(self) -> bool:
        if not self.master_file.exists():
            raise FileNotFoundError(
                f"Could not find Salt master file: {self.master_file}"
            )

        try:
            with open(self.master_file) as f:
                data: dict = json.load(f)

        except Exception as exc:
            log.error(
                Exception(
                    f"Unhandled exception reading Salt master file [{self.master_file}]. Details: {exc}"
                )
            )

            return False

        try:
            master: SaltMaster = SaltMaster.model_validate(data)

            log.debug(f"Loaded master: {master}")

            self.master = master

            return True

        except Exception as exc:
            log.error(
                Exception(
                    f"Unhandled exception converting master data to SaltMaster object. Details: {exc}.\nMaster data: {data}"
                )
            )

            return False

    def load_minions(self) -> bool:
        if not self.minions_file.exists():
            raise FileNotFoundError(
                f"Could not find Salt minions file: {self.minions_file}"
            )

        try:
            with open(self.minions_file) as f:
                data: list[dict] = json.load(f)

        except Exception as exc:
            log.error(
                Exception(
                    f"Unhandled exception reading Salt minions file [{self.minions_file}]. Details: {exc}"
                )
            )

            return False

        minions: list[SaltMinion] = []

        for _minion in data:
            try:
                minion: SaltMinion = SaltMinion.model_validate(_minion)

                minions.append(minion)
            except Exception as exc:
                log.error(
                    Exception(
                        f"Unhandled exception converting minion data to SaltMinion object. Details: {exc}.\Minion data: {_minion}"
                    )
                )

                return False

        self.minions = minions

        log.info(
            f"Loaded [{len(minions)}] Salt minion(s) to Inventory. Data loaded from file: {self.minions_file}"
        )

        return True


class SaltInventory(SaltInventoryBase):
    @property
    def count_minions(self) -> int:
        if self.minions is None:
            return 0
        else:
            return len(self.minions)


class SaltInventoryObjectBase(BaseModel):
    name: str | None = Field(default=None)
    host: str | None = Field(default=None)
    os_type: str | None = Field(default=None)
    distro: str | None = Field(default=None)

    def reachable(self) -> bool:
        """Attempt an ICMP ping request, using the object's 'host' parameter."""
        with SimpleSpinner(
            f"Pinging [{self.name}] || If you're seeing this, the host is likely unreachable. A successful ping is close to instant"
        ):
            return ping(self.host)


class SaltMaster(SaltInventoryObjectBase):
    pass


class SaltMinion(SaltInventoryObjectBase):
    pass

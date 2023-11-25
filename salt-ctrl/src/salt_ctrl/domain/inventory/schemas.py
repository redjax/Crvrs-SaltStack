from __future__ import annotations

import json

from pathlib import Path
from typing import Union

from salt_ctrl.constants import INVENTORY_DIR
from salt_ctrl.utils.net_utils import ping

from loguru import logger as log
from pydantic import BaseModel, Field, ValidationError, field_validator
from red_utils.ext.context_managers.cli_spinners import SimpleSpinner
from red_utils.ext.msgpack_utils import (
    msgpack_serialize,
    msgpack_serialize_file,
    msgpack_deserialize,
    msgpack_deserialize_file,
    default_serialize_dir,
)
from red_utils.std.hash_utils import get_hash_from_str


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

    def serialize(self, to_disk: bool = False, overwrite: bool = False) -> bytes:
        """Serialize inventory objects with msgpack.

        Returns a bytestring. Optionally, serialize to an output file.
        """
        log.info(f"Serializing inventory object {self.name} ({type(self).__name__})")

        try:
            data: str = self.model_dump_json()
        except Exception as exc:
            msg = Exception(
                f"Unhandled exception dumping ({type(self).__name__}) object to JSON. Details: {exc}"
            )
            log.error(msg)

            raise msg

        try:
            serial = msgpack_serialize(_json=data)
        except Exception as exc:
            msg = Exception(
                f"Unhandled exception serializing ({type(self).__name__}) object. Details: {exc}"
            )
            log.error(msg)

            raise msg

        if not serial.success:
            msg = Exception(
                f"Unhandled exception serializing inventory object. Details: {serial.detail}"
            )
            log.error(msg)

            raise msg

        if not to_disk:
            return serial.detail

        else:
            filename: str = f"{self.name}.msgpack"

            if isinstance(self, SaltMaster):
                obj_type: str = "master"
            elif isinstance(self, SaltMinion):
                obj_type: str = "minion"
            else:
                obj_type: str = "unknown"

            match obj_type:
                case "master":
                    output_path: Path = Path(
                        f"{default_serialize_dir}/inventory/masters/{filename}"
                    )
                case "minion":
                    output_path: Path = Path(
                        f"{default_serialize_dir}/inventory/minions/{filename}"
                    )
                case "unknown":
                    output_path: Path = Path(
                        f"{default_serialize_dir}/inventory/uncategorized/{filename}"
                    )
                case _:
                    output_path: Path = Path(
                        f"{default_serialize_dir}/inventory/uncategorized/{filename}"
                    )

            if not output_path.exists():
                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                except PermissionError as perm:
                    msg = PermissionError(
                        f"Permission denied creating directory path '{output_path.parent}'. Details: {perm}"
                    )
                    log.error(msg)

                    raise msg
                except Exception as exc:
                    msg = Exception(
                        f"Unhandled exception creating directory path '{output_path.parent}'. Details: {exc}"
                    )
                    log.error(msg)

                    raise msg

                try:
                    with open(output_path, "wb+") as f:
                        f.write(serial.detail)
                except Exception as exc:
                    msg = Exception(
                        f"Unhandled exception writing serialized object to file {output_path}. Details: {exc}"
                    )
                    log.error(msg)

                    raise msg

                return serial.detail

            else:
                log.warning(
                    f"to_disk is True, but file already exists at {output_path}"
                )

                if overwrite:
                    log.warning(
                        f"overwrite is True, overwriting contents of file at {output_path}"
                    )

                    try:
                        with open(output_path, "wb+") as f:
                            f.write(serial.detail)
                    except Exception as exc:
                        msg = Exception(
                            f"Unhandled exception writing serialized object to file {output_path}. Details: {exc}"
                        )
                        log.error(msg)

                        raise msg

                return serial.detail


class SaltMaster(SaltInventoryObjectBase):
    pass


class SaltMinion(SaltInventoryObjectBase):
    pass

from __future__ import annotations

import json

from pathlib import Path
from typing import Union

from salt_ctrl.constants import INVENTORY_DIR, PQ_DIR
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

import pandas as pd


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

    def master_df(self) -> pd.DataFrame:
        """Compile a SaltMaster object to a DataFrame.

        Converts SaltMaster to a Python dict, then creates a DataFrame from
        this dict.
        """
        if self.master is None:
            log.warning(f"Inventory Salt master is None. Loading Salt master.")
            self.load_master()

        log.debug(f"Compiling Salt master to DataFrame")

        dump_master: dict = self.master.model_dump()
        dump_master["salt_type"] = "master"
        dump_master["serialized"] = self.master.serialize()

        master_df: pd.DataFrame = pd.DataFrame.from_dict(dump_master, orient="index").T
        # log.debug(f"Master DataFrame:\n{master_df}")

        return master_df

    def minions_df(self) -> pd.DataFrame:
        """Compile a list of SaltMinion objects to a single DataFrame.

        Function loops over SaltMinion objects in salt_minions, converting each to a Python
        dict and appending "salt_type": "minion" to each object; a DataFrame is created from
        this dict, then added to a temporary list.

        Once looping through the list is complete, a single DataFrame is created by concatenating
        each minion DataFrame.
        """
        if self.minions is None:
            log.warning(f"Inventory Salt minions list is None. Loading Salt minions.")
            self.load_minions()

        log.debug(f"Compiling [{len(self.minions)}] Salt minion(s) to DataFrame")
        minion_dfs: list[pd.DataFrame] = []

        for minion in self.minions:
            dump_minion: dict = minion.model_dump()
            dump_minion["salt_type"] = "minion"
            dump_minion["serialized"] = minion.serialize()
            # log.debug(f"Minion dump ({type(dump_minion)}): {dump_minion}")

            _df: pd.DataFrame = pd.DataFrame.from_dict(dump_minion, orient="index").T
            # log.debug(f"Minion DataFrame:\n{_df}")
            minion_dfs.append(_df)
        log.debug(f"Compiled [{len(minion_dfs)}] minion DataFrame(s)")

        minions_df: pd.DataFrame = pd.concat(minion_dfs)
        log.debug(f"Compiled [{minions_df.shape[0]}] Salt minions to single DataFrame")

        return minions_df


class SaltInventory(SaltInventoryBase):
    @property
    def count_minions(self) -> int:
        if self.minions is None:
            return 0
        else:
            return len(self.minions)

    def df(self, to_disk: bool = False, overwrite: bool = False) -> pd.DataFrame:
        """Compile Salt master & minions to a single DataFrame.

        Optionally, save to a Parquet file by passing to_disk=True. If the
        DataFrame has already been saved, this function will skip saving the
        Parquet file unless overwrite=True is passed.
        """
        master_df: pd.DataFrame = self.master_df()
        minions_df: pd.DataFrame = self.minions_df()

        inventory_df: pd.DataFrame = pd.concat([master_df, minions_df])

        if to_disk:
            output_file: Path = Path(f"{PQ_DIR}/inventory.parquet")

            if output_file.exists():
                if not overwrite:
                    log.warning(
                        f"Output file already exists: {output_file}. Overwrite is False, skipping save"
                    )
                else:
                    log.info(f"Saving DataFrame to {output_file}")

                    try:
                        inventory_df.to_parquet(path=output_file, engine="fastparquet")
                    except Exception as exc:
                        msg = Exception(
                            f"Unhandled exception saving inventory DataFrame to file {output_file}. Details: {exc}"
                        )
                        log.error(msg)

            else:
                log.info(f"Saving DataFrame to {output_file}")

                try:
                    inventory_df.to_parquet(path=output_file, engine="fastparquet")
                except Exception as exc:
                    msg = Exception(
                        f"Unhandled exception saving inventory DataFrame to file {output_file}. Details: {exc}"
                    )
                    log.error(msg)

        return inventory_df


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

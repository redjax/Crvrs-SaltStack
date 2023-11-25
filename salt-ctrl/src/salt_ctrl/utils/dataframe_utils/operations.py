from __future__ import annotations

from typing import Union, TYPE_CHECKING
from pathlib import Path

from loguru import logger as log
import pandas as pd

from salt_ctrl.constants import DATA_DIR, PQ_DIR

if TYPE_CHECKING:
    from salt_ctrl.domain.inventory import SaltInventory, SaltMaster, SaltMinion


def compile_minions_df(salt_minions: list[SaltMinion] = None) -> pd.DataFrame:
    """Compile a list of SaltMinion objects to a single DataFrame.

    Function loops over SaltMinion objects in salt_minions, converting each to a Python
    dict and appending "salt_type": "minion" to each object; a DataFrame is created from
    this dict, then added to a temporary list.

    Once looping through the list is complete, a single DataFrame is created by concatenating
    each minion DataFrame.
    """
    if salt_minions is None:
        raise ValueError("Missing list of SaltMinion objects")

    log.debug(f"Compiling [{len(salt_minions)}] Salt minion(s) to DataFrame")
    minion_dfs: list[pd.DataFrame] = []

    for minion in salt_minions:
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


def compile_master_df(salt_master: SaltMaster = None) -> pd.DataFrame:
    """Compile a SaltMaster object to a DataFrame.

    Converts SaltMaster to a Python dict, then creates a DataFrame from
    this dict.
    """
    if salt_master is None:
        raise ValueError("Missing SaltMaster object")

    log.debug(f"Compiling Salt master to DataFrame")

    dump_master: dict = salt_master.model_dump()
    dump_master["salt_type"] = "master"
    dump_master["serialized"] = salt_master.serialize()

    master_df: pd.DataFrame = pd.DataFrame.from_dict(dump_master, orient="index").T
    log.debug(f"Master DataFrame:\n{master_df}")

    return master_df


def compile_inventory_df(
    salt_inventory: SaltInventory = None, to_disk: bool = False, overwrite: bool = False
) -> pd.DataFrame:
    if salt_inventory is None:
        raise ValueError("Missing SaltInventory object")

    master_df: pd.DataFrame = compile_master_df(salt_master=salt_inventory.master)
    minions_df: pd.DataFrame = compile_minions_df(salt_minions=salt_inventory.minions)

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

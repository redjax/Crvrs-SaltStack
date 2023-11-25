from __future__ import annotations

from typing import Union, TYPE_CHECKING
from pathlib import Path

from loguru import logger as log
import pandas as pd


def dict_to_df(input_dict: dict = None) -> pd.DataFrame:
    try:
        df: pd.DataFrame = pd.DataFrame.from_dict(input_dict, orient="index").T

        return df
    except Exception as exc:
        msg = Exception(
            f"Unhandled exception converting input dict to DataFrame. Details: {dict({'exception': {exc}, 'input_dict': {input_dict}})}"
        )
        log.error(msg)


def list_dicts_to_df(input_list: list[dict] = None) -> pd.DataFrame:
    tmp_dfs: list[pd.DataFrame] = []

    for i in input_list:
        _df: pd.DataFrame = dict_to_df(input_dict=i)
        tmp_dfs.append(_df)

    df: pd.DataFrame = concat_dfs(tmp_dfs)

    return df


def concat_dfs(dfs: list[pd.DataFrame] = None) -> pd.DataFrame:
    try:
        df: pd.DataFrame = concat_dfs(dfs)

        return df
    except Exception as exc:
        msg = Exception(
            f"Unhandled exception concatenating list of Pandas DataFrame objects. Details: {exc}"
        )
        log.error(msg)

from __future__ import annotations

import platform
import subprocess

from loguru import logger as log

def ping(host: str = None):
    """Attempt to reach a specified host."""
    if host is None:
        raise ValueError(f"Missing host to ping. Pass a hostname/FQDN or IP address.")

    if not isinstance(host, str):
        raise TypeError(
            f"Invalid type for host param: {type(host)}. Must be of type str."
        )

    ## Set ping option based on OS type
    param: str = "-n" if platform.system().lower() == "windows" else "-c"

    command: list[str] = ["ping", param, "1", host]

    try:
        response: int = (
            subprocess.call(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            == 0
        )

        return response

    except Exception as exc:
        log.error(
            Exception(f"Unhandled exception pinging host [{host}]. Details: {exc}")
        )

        return False

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union

from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger as log

## Import class definitions for editor type hinting, without fully importing the module
if TYPE_CHECKING:
    from salt_ctrl.domain.inventory import SaltInventory, SaltMaster, SaltMinion

from salt_ctrl.constants import SALT_FW_PORTS, TEMPLATE_OUTPUT_DIR
from salt_ctrl.utils.jinja_utils import (
    get_loader_env,
    load_template,
    load_template_dir,
    render_template,
)

def render_master_scripts(
    salt_master: SaltMaster = None,
    template_env: Environment = None,
    output_dir: Union[Path, str] = None,
) -> None:
    """Load Jinja templates for Salt master and render scripts to output directory.

    A subdirectory with the master's name will be created in the output_dir subdirectory
    /masters.
    """
    if salt_master is None:
        raise ValueError("Missing SaltMaster object")
    if template_env is None:
        raise ValueError("Missing template loader environment")
    if output_dir is None:
        raise ValueError(f"Missing output file path/name")

    if isinstance(output_dir, str):
        output_dir: Path = Path(output_dir)

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        install_master_templ = load_template(
            template_env=template_env,
            template_file="install_master.j2",
        )

        allow_ports_templ = load_template(
            template_env=template_env, template_file="allow_ports.j2"
        )

        if salt_master.os_type == "linux":
            render_template(
                template=install_master_templ,
                outfile=f"{output_dir}/install_master.sh",
                data={"master": salt_master},
            )

            render_template(
                template=allow_ports_templ,
                outfile=f"{output_dir}/allow_ports.sh",
                data={"ports": SALT_FW_PORTS},
            )
        else:
            raise NotImplementedError(
                f"Support for OS type [{salt_master.os_type}] not yet implemented."
            )

    except Exception as exc:
        raise Exception(f"Unhandled exception rendering template data. Details: {exc}")


def render_minion_scripts(
    salt_master: SaltMaster = None,
    salt_minions: list[SaltMinion] = None,
    template_env: Environment = None,
) -> None:
    """Load Jinja templates for Salt master and render scripts to output directory.

    Note: With minions, the output directory is created automatically. The output directory
    path is concatenated from the TEMPLATE_OUTPUT_DIR constant, with /minions as a subdirectory.

    The function loops over a salt_minions list object and creates a directory for each minion.
    """
    if salt_master is None:
        raise ValueError(f"Missing SaltMaster object")
    if salt_minions is None:
        raise ValueError("Missing list of SaltMinion objects")
    if template_env is None:
        raise ValueError("Missing template loader environment")

    allow_ports_templ = load_template(
        template_env=template_env, template_file="allow_ports.j2"
    )

    for minion in salt_minions:
        output_dir: Path = Path(f"{TEMPLATE_OUTPUT_DIR}/minions/{minion.name}")

        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        try:
            install_minion_templ = load_template(
                template_env=template_env, template_file="install_minion.j2"
            )
            render_template(
                template=install_minion_templ,
                outfile=f"{output_dir}/install_minion.sh",
                data={"master": salt_master},
            )

            render_template(
                template=allow_ports_templ,
                outfile=f"{output_dir}/allow_ports.sh",
                data={"ports": SALT_FW_PORTS},
            )
        except Exception as exc:
            raise Exception(
                f"Unhandled exception rendering scripts for minion [{minion.name}]. Details: {exc}"
            )


def render_inventory_scripts(
    inventory: SaltInventory = None, template_loader: FileSystemLoader = None
) -> bool:
    """Render master and minion scripts from Jinja templates."""
    if inventory is None:
        raise ValueError("Missing SaltInventory object")
    if template_loader is None:
        raise ValueError(f"Missing Jinja2 FileSystemLoader")

    LOADER_ENV = get_loader_env(loader=template_loader)

    MASTER: SaltMaster = inventory.master
    MINIONS: list[SaltMinion] = inventory.minions

    try:
        render_master_scripts(
            salt_master=MASTER,
            template_env=LOADER_ENV,
            output_dir=f"{TEMPLATE_OUTPUT_DIR}/masters/{MASTER.name}",
        )
    except Exception as exc:
        msg = Exception(f"Unhandled exception rendering master scripts. Details: {exc}")
        log.error(msg)

        return False

    try:
        render_minion_scripts(
            salt_master=MASTER, salt_minions=MINIONS, template_env=LOADER_ENV
        )
    except Exception as exc:
        msg = Exception(f"Unhandled exception rendering minion scripts. Details: {exc}")
        log.error(msg)

        return False

    return True

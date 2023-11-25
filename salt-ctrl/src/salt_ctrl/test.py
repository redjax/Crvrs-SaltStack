from __future__ import annotations

import sys

sys.path.append(".")

from pathlib import Path
from typing import Union

from salt_ctrl.constants import (
    DATA_DIR,
    PQ_DIR,
    SALT_FW_PORTS,
    SCRIPT_TEMPLATES_DIR,
    SETUP_TEMPLATES_DIR,
    TEMPLATE_OUTPUT_DIR,
    TEMPLATES_DIR,
)
from salt_ctrl.core import AppSettings
from salt_ctrl.core.salt_nodes import (
    SALT_MASTER,
    SALT_MASTER_ADDRESS,
    SALT_MINIONS,
    inventory,
)
from salt_ctrl.domain.inventory import SaltInventory, SaltMaster, SaltMinion
from salt_ctrl.utils.jinja_utils import (
    get_loader_env,
    load_template,
    load_template_dir,
    render_template,
)
from salt_ctrl.utils.salt_inventory_utils import (
    render_inventory_scripts,
    render_master_scripts,
    render_minion_scripts,
)
from salt_ctrl.utils.dataframe_utils import (
    compile_minions_df,
    compile_inventory_df,
    compile_master_df,
)

from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger as log
from red_utils.ext.loguru_utils import (
    LoguruSinkAppFile,
    LoguruSinkErrFile,
    LoguruSinkStdOut,
    init_logger,
)

app_settings: AppSettings = AppSettings()

ensure_dirs: list[Path] = [
    DATA_DIR,
    PQ_DIR,
    TEMPLATES_DIR,
    TEMPLATE_OUTPUT_DIR,
    SCRIPT_TEMPLATES_DIR,
    SETUP_TEMPLATES_DIR,
]

for d in ensure_dirs:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    init_logger(sinks=[LoguruSinkStdOut(level=app_settings.log_level).as_dict()])

    log.info(
        f"[env:{app_settings.env}|container:{app_settings.container_env}] App start"
    )
    log.debug(f"App settings: {app_settings}")
    log.debug(f"Templates dir {TEMPLATES_DIR} exists: {TEMPLATES_DIR.exists()}")

    log.debug(f"Salt master: {SALT_MASTER}")
    log.debug(f"Salt minions: {SALT_MINIONS}")

    LOADER = load_template_dir(templates_dir=f"{TEMPLATES_DIR}/scripts/setup/linux")

    render_inventory: bool = render_inventory_scripts(
        inventory=inventory, template_loader=LOADER
    )
    log.info(f"Render inventory success: {render_inventory}")

    master_df = compile_master_df(salt_master=inventory.master)
    log.debug(f"Master DataFrame:\n{master_df}")

    minions_df = compile_minions_df(salt_minions=inventory.minions)
    log.debug(f"Minions DataFrame:\n{minions_df}")

    inventory_df = compile_inventory_df(
        salt_inventory=inventory, to_disk=True, overwrite=True
    )
    log.debug(f"Full inventory DataFrame:\n{inventory_df}")

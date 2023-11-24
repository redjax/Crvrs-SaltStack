import sys

sys.path.append(".")

from typing import Union
from pathlib import Path

from loguru import logger as log
from red_utils.ext.loguru_utils import (
    init_logger,
    LoguruSinkAppFile,
    LoguruSinkErrFile,
    LoguruSinkStdOut,
)

from salt_ctrl.core import AppSettings
from salt_ctrl.constants import (
    TEMPLATES_DIR,
    TEMPLATE_OUTPUT_DIR,
    SALT_FW_PORTS,
    SCRIPT_TEMPLATES_DIR,
    SETUP_TEMPLATES_DIR,
)

from salt_ctrl.salt_nodes import (
    SALT_MASTER_ADDRESS,
    SALT_MINIONS,
    SALT_MASTER,
    inventory,
)

from salt_ctrl.utils.jinja_utils import (
    load_template_dir,
    load_template,
    get_loader_env,
    render_template,
)
from salt_ctrl.utils.salt_inventory_utils import (
    render_inventory_scripts,
    render_master_scripts,
    render_minion_scripts,
)
from salt_ctrl.domain.inventory import SaltInventory, SaltMaster, SaltMinion

from jinja2 import Template, Environment, FileSystemLoader

app_settings: AppSettings = AppSettings()

ensure_dirs: list[Path] = [
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

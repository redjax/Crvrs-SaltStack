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
from salt_ctrl.constants import TEMPLATES_DIR, TEMPLATE_OUTPUT_DIR
from salt_ctrl.salt_nodes import SALT_MASTER_ADDRESS, SALT_MINIONS, SALT_MASTER

from jinja2 import Template, FileSystemLoader, Environment

app_settings: AppSettings = AppSettings()

if not TEMPLATE_OUTPUT_DIR.exists():
    TEMPLATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_template_dir(
    templates_dir: Union[Path, str] = TEMPLATES_DIR
) -> FileSystemLoader:
    """Create loader for Jinja to open .j2 files."""
    if not templates_dir:
        raise ValueError("Missing templates_dir")

    if isinstance(templates_dir, str):
        templates_dir: Path = Path(templates_dir)

    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    try:
        loader: FileSystemLoader = FileSystemLoader(searchpath=templates_dir)
    except Exception as exc:
        raise Exception(
            f"Unhandled exception getting Jinja FileSystemLoader. Details: {exc}"
        )

    return loader


def get_loader_env(loader: FileExistsError = load_template_dir()) -> Environment:
    """Create a Jinja2.Environment object for Jinja template loader object.

    Environment is used to pass data & output a templated file.
    """

    if not loader:
        raise ValueError("Jinja FileSystemLoader object missing")

    try:
        env: Environment = Environment(loader=loader)
    except Exception as exc:
        raise Exception(
            f"Unhandled exception getting Jinja template Environment. Details: {exc}"
        )

    return env


def load_template(
    template_env: Environment = get_loader_env(), template_file: str = None
) -> Template:
    """Create a Python object for Jinja template.

    This template can be rendered to a file. Values can be passed from Python variables.
    """
    if not template_env:
        raise ValueError("Jinja Environment object missing")

    if not template_file:
        raise ValueError("Missing path to a .j2 template file")

    try:
        template: Template = template_env.get_template(template_file)
    except FileNotFoundError as fnf:
        raise FileNotFoundError(
            f"Could not find template file by name '{template_file}'. Details: {fnf}"
        )
    except Exception as exc:
        raise Exception(
            f"Unhandled exception loading Template '{template_file}' from Environment. Details: {exc}"
        )

    return template


def render_template(
    template: Template = None, outfile: Union[str, Path] = None
) -> bool:
    """Render a .j2 template to an output file."""
    if not template:
        raise ValueError("Missing Jinja Template object")
    if not outfile:
        raise ValueError("Missing output file path")

    if isinstance(outfile, str):
        outfile: Path = Path(outfile)

    if outfile.exists():
        log.warning(f"Output file '{outfile}' already exists. Skipping render.")
        return False

    try:
        render = template.render()

        with open(outfile, "w") as out:
            out.write(render)

    except Exception as exc:
        raise Exception(
            f"Unhandled exception rendering template to file '{outfile}'. Details: {exc}"
        )


if __name__ == "__main__":
    init_logger(sinks=[LoguruSinkStdOut(level=app_settings.log_level).as_dict()])

    log.info(
        f"[env:{app_settings.env}|container:{app_settings.container_env}] App start"
    )
    log.debug(f"App settings: {app_settings}")
    log.debug(f"Templates dir {TEMPLATES_DIR} exists: {TEMPLATES_DIR.exists()}")

    log.debug(f"Salt master: {SALT_MASTER}")
    log.debug(f"Salt minions: {SALT_MINIONS}")

    LOADER = load_template_dir(templates_dir=f"{TEMPLATES_DIR}/scripts/setups/linux")
    LOADER_ENV = get_loader_env(loader=LOADER)
    install_master_templ = load_template(
        template_env=LOADER_ENV, template_file="install_master.j2"
    )

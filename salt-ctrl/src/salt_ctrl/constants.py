from __future__ import annotations

from pathlib import Path

TEMPLATES_DIR: Path = Path("templates")
TEMPLATE_OUTPUT_DIR: Path = Path("output/templates")
INVENTORY_DIR: Path = Path("inventory")
MINIONS_FILE: Path = Path(f"{INVENTORY_DIR}/minions.json")
MASTERS_FILE: Path = Path(f"{INVENTORY_DIR}/masters.json")

SALT_FW_PORTS: list[int] = [4505, 4506]

SCRIPT_TEMPLATES_DIR: Path = Path(f"{TEMPLATES_DIR}/scripts")
SCRIPT_OUTPUT_DIR: Path = Path(f"output/scripts")
SETUP_TEMPLATES_DIR: Path = Path(f"{SCRIPT_TEMPLATES_DIR}/setup")

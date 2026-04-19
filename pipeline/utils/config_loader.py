from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


DEFAULT_DATASET_CONFIG_PATH = Path("config/datasets.yml")


def load_dataset_config(
    accession: str,
    config_path: str | Path = DEFAULT_DATASET_CONFIG_PATH,
) -> dict[str, Any]:
    config_path = Path(config_path)

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    for dataset in config["datasets"]:
        if dataset["accession"] == accession:
            return dataset

    raise ValueError(f"Dataset config not found: {accession}")
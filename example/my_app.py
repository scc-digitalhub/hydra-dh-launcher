# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import time

import hydra
from omegaconf import DictConfig

log = logging.getLogger(__name__)


@hydra.main(version_base=None, config_path=".", config_name="config")
def my_app(cfg: DictConfig) -> None:
    x: float = cfg.x
    y: float = cfg.y

    if cfg.get("error", False):
        raise RuntimeError("cfg.error is True")

    return x**2 + y**2


if __name__ == "__main__":
    my_app()

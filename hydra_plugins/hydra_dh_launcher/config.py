# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
# Copyright (C) Facebook, Inc. and its affiliates. All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from typing import Optional

from hydra.core.config_store import ConfigStore


@dataclass
class DHLauncherConf:
    _target_: str = "hydra_plugins.hydra_dh_launcher.dh_launcher.DHLauncher"

    # maximum number of concurrently running jobs. if -1, all CPUs are used
    n_jobs: int = -1

    # name of the project. Required field for DHLauncher
    project_name: str = ""
    # name of the function to run. Required field for DHLauncher
    function: str = ""
    # main job id
    job_ref: Optional[str] = None

    # volumes to mount to the container
    volumes: list[dict]| None = field(default_factory=list)
    # resources to assign to the container
    resources: dict | None = field(default_factory=dict)
    # environment variables
    envs: list[dict] | None = field(default_factory=list)
    # secrets to pass to the container
    secrets: list[str] | None = field(default_factory=list)
    # resource profile
    profile: str | None = None

    # local execution is used for testing and debugging. It will run the function in the same process instead of launching a separate job.
    local_execution: bool = False


ConfigStore.instance().store(
    group="hydra/launcher",
    name="dh",
    node=DHLauncherConf,
    provider="dhlauncher",
)

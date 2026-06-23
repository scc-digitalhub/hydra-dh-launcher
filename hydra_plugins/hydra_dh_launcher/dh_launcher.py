# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import logging
from typing import Any, Optional, Sequence, cast

from hydra.core.utils import JobReturn
from hydra.plugins.launcher import Launcher
from hydra.types import HydraContext, TaskFunction
from omegaconf import DictConfig

log = logging.getLogger(__name__)


class DHLauncher(Launcher):
    def __init__(self, **kwargs: Any) -> None:
        """DigitalHub Launcher

        """
        self.config: Optional[DictConfig] = None
        self.task_function: Optional[TaskFunction] = None
        self.hydra_context: Optional[HydraContext] = None

        self.dh = kwargs

    def setup(
        self,
        *,
        hydra_context: HydraContext,
        task_function: TaskFunction,
        config: DictConfig,
    ) -> None:
        self.config = config
        self.task_function = task_function
        self.hydra_context = hydra_context

    def launch(
        self, job_overrides: Sequence[Sequence[str]], initial_job_idx: int
    ) -> Sequence[JobReturn]:
        from . import _core

        return _core.launch(
            launcher=cast(Any, self),
            job_overrides=job_overrides,
            initial_job_idx=initial_job_idx,
        )

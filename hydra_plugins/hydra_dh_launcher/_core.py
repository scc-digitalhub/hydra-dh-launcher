# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
# Copyright (C) Facebook, Inc. and its affiliates. All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
from typing import Any, Dict, List, Sequence
import re

from hydra.core.singleton import Singleton
from hydra.core.utils import (
    JobReturn,
    JobStatus,
    configure_log,
    filter_overrides,
    run_job,
    setup_globals,
)
from hydra.types import HydraContext

from omegaconf import DictConfig, OmegaConf, open_dict

from .dh_launcher import DHLauncher

import os
import digitalhub as dh


log = logging.getLogger(__name__)

def execute_job(
    idx: int,
    overrides: Sequence[str],
    hydra_context: HydraContext,
    config: DictConfig,
    func_config: DictConfig,
    func,
    singleton_state: Dict[Any, Any],
) -> JobReturn:
    """Calls `run_job` in parallel"""
    setup_globals()
    Singleton.set_state(singleton_state)

    sweep_config = hydra_context.config_loader.load_sweep_config(
        config, list(overrides)
    )

    job_id = f"{sweep_config.hydra.job.name}_{idx}"
    job_num = idx

    with open_dict(sweep_config):
        sweep_config.hydra.job.id = job_id
        sweep_config.hydra.job.num = job_num

    output_dir = str(OmegaConf.select(sweep_config, "hydra.sweep.dir"))
    subdir = str(OmegaConf.select(sweep_config, "hydra.sweep.subdir"))
    output_subdir = str(OmegaConf.select(sweep_config, "hydra.output_subdir"))
    output_dir = os.path.join(output_dir, subdir, output_subdir)
    job_dir = os.path.abspath(output_dir)

    def task_function(cfg: DictConfig) -> Any:
        local_execution = func_config.get("local_execution", False)

        run = func.run(action="subtask", 
            wait=local_execution, 
            log_info=False,
            volumes=func_config.get("volumes", None),
            resources=func_config.get("resources", None),
            envs=func_config.get("envs", None),
            secrets=func_config.get("secrets", None),
            profile=func_config.get("profile", None),
            parameters={
                "cfg_passthrough": OmegaConf.to_container(cfg),
                "job_id": job_id,
                "job_num": job_num,
                "job_dir": job_dir,
                },
            job_ref=func_config.get("job_ref", None),
            local_execution=local_execution,
        )
        status = run.refresh().status
        if status.state == "ERROR":
            raise RuntimeError(f"Job failed with error: {status.message or 'Execution error'}")

        if local_execution:
            values = [v for k, v in status.results.items()]
            if len(status.results) == 1:
                return values[0]
            else:   
                return values
        else:
            return run.id

    ret = run_job(
        hydra_context=hydra_context,
        config=sweep_config,
        task_function=task_function,
        job_dir_key="hydra.sweep.dir",
        job_subdir_key="hydra.sweep.subdir",
    )

    return ret


def _get_function_signature(function: str) -> tuple[str, str]:
    # check regex to make sure the function is in the correct format
    match = re.search(r"^[^:]+://[^/]+/[^/]+:.+$", function)
    if match:
        # function is in format <runtime>://<project_name>/<function_name>:<version>
        func_id = function.split("/")[-1]
        function_name = func_id.split(":")[0]
        version = func_id.split(":")[1]
        return function_name, version
    
    match = re.search(r"^[^:]+$", function)
    if match:
        # function is in format <function_name>, use default version
        return function, None

def run_and_monitor_remote_jobs(
        initial_job_idx: int,
        job_overrides: Sequence[Sequence[str]],
        hydra_context: HydraContext,
        config: DictConfig,
        func_config: DictConfig,
        project_name: str,
        func,
        singleton_state: Dict[Any, Any],
) -> Sequence[JobReturn]:
    """Run and monitor remote jobs.

    This function executes a series of remote jobs based on the provided job overrides and monitors their status until completion.
    If any job fails, a RuntimeError is raised.
    The function returns the results of all successfully completed jobs.

    Args:
        initial_job_idx (int): _description_
        job_overrides (Sequence[Sequence[str]]): _description_
        hydra_context (HydraContext): _description_
        config (DictConfig): _description_
        func_config (DictConfig): _description_
        project_name (str): _description_
        func (_type_): _description_
        singleton_state (Dict[Any, Any]): _description_

    Raises:
        RuntimeError: _description_

    Returns:
        Sequence[JobReturn]: _description_
    """
    runs = []
    for idx, overrides in enumerate(job_overrides):
        job_return = execute_job(
            initial_job_idx + idx,
            overrides,
            hydra_context,
            config,
            func_config,
            func,
            singleton_state,
        )
        if job_return.status != JobStatus.COMPLETED:
            raise RuntimeError(f"Job failed with status: {job_return.status}")
        runs.append(job_return)

    to_complete = len(runs)
    results = [None] * len(runs)
    project = dh.get_project(project_name)
    log.info(f"Monitoring {len(runs)} remote jobs.")

    while to_complete > 0:    
        for idx, job_return in enumerate(runs):
            # result has not been retrieved yet
            if results[idx] is None:
                run_id = job_return.return_value
                run = project.get_run(run_id)
                status = run.refresh().status
                if status.state == "ERROR":
                    raise RuntimeError(f"Job failed with error: {status.message or 'Execution error'}")
                if status.state == "COMPLETED":
                    values = [v for k, v in status.results.items()]
                    if len(status.results) == 1:
                        values = values[0]
                    job_return.return_value = values
                    results[idx] = job_return
                    to_complete -= 1
        time.sleep(10)
        log.info(f"{to_complete} jobs remaining.")
    return results

def launch(
    launcher: DHLauncher,
    job_overrides: Sequence[Sequence[str]],
    initial_job_idx: int,
) -> Sequence[JobReturn]:
    """
    :param job_overrides: a List of List<String>, where each inner list is the arguments for one job run.
    :param initial_job_idx: Initial job idx in batch.
    :return: an array of return values from run_job with indexes corresponding to the input list indexes.
    """
    setup_globals()
    assert launcher.config is not None
    assert launcher.task_function is not None
    assert launcher.hydra_context is not None

    import sys
    sys.argv = []

    configure_log(launcher.config.hydra.hydra_logging, launcher.config.hydra.verbose)
    sweep_dir = Path(str(launcher.config.hydra.sweep.dir))
    sweep_dir.mkdir(parents=True, exist_ok=True)


    dhlauncher_config = launcher.dh
    ## check if the function exists in the project
    ## recover function. 
    ## if exists, check the source code signature to make sure it is the same. Otherwise, create new version.
    project_name = dhlauncher_config['project_name']
    if project_name is None:
        raise ValueError("project_name is not set in the config.")


    function = dhlauncher_config['function']
    if not function:
        raise ValueError("function is not set in the config.")
    
    func = None
    function_name, version = _get_function_signature(function)
    try:
        func = dh.get_function(function_name, project=project_name, entity_id=version)
        # enforce task 
        func._get_or_create_task("subtask")
    except Exception:
        raise ValueError(f"Function {function} does not exist in project {project_name}.")
    
    n_jobs = dhlauncher_config.get("n_jobs", -1)
    max_workers = None if n_jobs == -1 else n_jobs

    log.info(
        "DigitalHub({}) is launching {} jobs".format(
            ",".join(f"{k}={v}" for k, v in dhlauncher_config.items()),
            len(job_overrides),
        )
    )
    log.info(f"Launching jobs, sweep output dir : {sweep_dir}")
    for idx, overrides in enumerate(job_overrides):
        log.info("\t#{} : {}".format(idx, " ".join(filter_overrides(overrides))))

    singleton_state = Singleton.get_state()

    runs: List[JobReturn] = [None] * len(job_overrides)  # type: ignore

    local_execution = dhlauncher_config.get("local_execution", False)
    # Execute jobs locally with thread pool executor and blocking
    if local_execution:
        futures_map = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for idx, overrides in enumerate(job_overrides):
                future = executor.submit(
                    execute_job,
                    initial_job_idx + idx,
                    overrides,
                    launcher.hydra_context,
                    launcher.config,
                    dhlauncher_config,
                    func,
                    singleton_state,
                )
                futures_map[future] = initial_job_idx + idx

        for future in as_completed(futures_map):
            idx = futures_map[future] - initial_job_idx
            runs[idx] = future.result()
    else:
        runs = run_and_monitor_remote_jobs(
            initial_job_idx,
            job_overrides,
            launcher.hydra_context,
            launcher.config,
            dhlauncher_config,
            project_name,
            func,
            singleton_state,
        )


    for run in runs:
        assert isinstance(run, JobReturn)
    return runs


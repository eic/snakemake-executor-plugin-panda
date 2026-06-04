__author__ = "Dmitry Kalinkin"
__copyright__ = "Copyright 2026, Dmitry Kalinkin"
__email__ = "dmitry.kalinkin+snakemake@gmail.com"
__license__ = "MIT"

import os
import shutil
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Generator, List, Optional

import snakemake
from snakemake_interface_common.exceptions import WorkflowError
from snakemake_interface_executor_plugins.executors.base import SubmittedJobInfo
from snakemake_interface_executor_plugins.executors.remote import RemoteExecutor
from snakemake_interface_executor_plugins.settings import (
    ExecutorSettingsBase,
    CommonSettings,
)
from snakemake_interface_executor_plugins.jobs import (
    JobExecutorInterface,
)

from pandaclient import Client, PrunScript

@dataclass
class ExecutorSettings(ExecutorSettingsBase):
    pre_script: Optional[str] = field(
        default="unset PYTHONPATH; source /cvmfs/eic.opensciencegrid.org/snakemake/9.20/setup.sh; export DETECTOR_PATH=/opt/detector/epic-main/share/epic; export DETECTOR_CONFIG=epic",
        metadata={
            "help": "Snakemake payload initialization",
            "required": False,
        },
    )

common_settings = CommonSettings(
    # define whether your executor plugin executes locally
    # or remotely. In virtually all cases, it will be remote execution
    # (cluster, cloud, etc.). Only Snakemake's standard execution
    # plugins (snakemake-executor-plugin-dryrun, snakemake-executor-plugin-local)
    # are expected to specify False here.
    non_local_exec=True,
    # Whether the executor implies to not have a shared file system
    implies_no_shared_fs=True,
    # whether to deploy workflow sources to default storage provider before execution
    job_deploy_sources=True,
    # whether arguments for setting the storage provider shall be passed to jobs
    pass_default_storage_provider_args=True,
    # whether arguments for setting default resources shall be passed to jobs
    pass_default_resources_args=True,
    # whether environment variables shall be passed to jobs (if False, use
    # self.envvars() to obtain a dict of environment variables and their values
    # and pass them e.g. as secrets to the execution backend)
    pass_envvar_declarations_to_cmd=True,
    # whether the default storage provider shall be deployed before the job is run on
    # the remote node. Usually set to True if the executor does not assume a shared fs
    auto_deploy_default_storage_provider=True,
    # specify initial amount of seconds to sleep before checking for job status
    init_seconds_before_status_checks=0,
)

class Executor(RemoteExecutor):
    def __post_init__(self):
        pass

    def get_python_executable(self):
        return "/usr/bin/env python3"

    def run_job(self, job: JobExecutorInterface):
        jobscript = self.get_jobscript(job)
        self.write_jobscript(job, jobscript)
        with open(jobscript, "rt") as fp:
            s = fp.read()

        s = s.replace("pip install --target '.snakemake/pip-deployments' snakemake-storage-plugin-rucio && ", "")

        with open(jobscript, "wt") as fp:
            fp.write(s)

        prun_args = [
            "--exec", f"{self.workflow.executor_settings.pre_script}; sh -x ./{Path(jobscript).name} && sh -c 'echo done > dummy'",
            "--outDS", f"user.veprbl.{uuid.uuid1()}",
            "--nJobs", "1",
            "--vo", os.getenv('PANDA_VO', 'wlcg'),
            "--site", os.getenv('PANDA_SITE', 'BNL_PanDA_1'),
            "--prodSourceLabel", "test",
            "--workingGroup", os.getenv('PANDA_AUTH_VO', 'wlcg'),
            "--noBuild",
            "--workDir", str(Path(jobscript).parent),
            "--outputs", "dummy",
        ]

        prev = Path.cwd()
        os.chdir(Path(jobscript).parent)
        params = PrunScript.main(True, prun_args)
        os.chdir(prev)
        params["maxAttempt"] = 1
        params["processingType"] = "snakemake_plugin"
        params["ramCount"] = 3096

        status, result = Client.insertTaskParams(params)

        if status != 0:
            raise RuntimeError(f"Job submission error: {result}")

        jedi_task_id = result[2]
        if jedi_task_id is None:
            jedi_task_id = result[1]

        print("Task id", jedi_task_id)
        job_info = SubmittedJobInfo(
            job,
            aux={
                "jobscript": jobscript,
            },
            external_jobid=jedi_task_id,
        )
        self.report_job_submission(job_info)

    async def check_active_jobs(
        self, active_jobs: List[SubmittedJobInfo]
    ) -> Generator[SubmittedJobInfo, None, None]:
        success = "success"
        failed = "failed"
        running = "running"

        for active_job in active_jobs:
            async with self.status_rate_limiter:
                status, result = Client.getTaskStatus(active_job.external_jobid)
                if status != 0:
                    print(f"Job query error: {result}")
                if result == "failed":
                    self.report_job_error(active_job)
                elif result == "done":
                    self.report_job_success(active_job)
                else:
                    yield active_job

    def cancel_jobs(self, active_jobs: List[SubmittedJobInfo]):
        for active_job in active_jobs:
            Client.killTask(active_job.external_jobid)

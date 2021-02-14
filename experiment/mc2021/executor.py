import inspect
import os
from pathlib import Path

from loguru import logger

import reprobench
from reprobench.tools.executable import ExecutableTool


class PrefExec(ExecutableTool):
    name = "MC Preprocessor"
    path="./pref_retcode_wrapper.sh"

    def __init__(self, context):
        super().__init__(context)
        self.output=self.parameters.get('output')

    def get_arguments(self):
        return [f"{self.prefix}{key} {value}" for key, value in self.parameters.items()]

    def get_cmdline(self):
        logger.warning(self.get_path())
        logger.trace(self.get_arguments())
        solver=self.parameters['solver']
        cmd=self.parameters['cmd'].replace("{solver}", solver)
        return [self.get_path() + " " + cmd]

    def run(self, executor):
        my_env = os.environ.copy()
        self.run_internal(executor, my_env)

    def run_internal(self, executor, environment):
        logger.debug([*self.get_cmdline(), self.task])

        executor.run(
            self.get_cmdline(),
            directory=self.cwd,
            input_str="%s" %self.task,
            out_path=self.get_out_path(),
            err_path=self.get_err_path(),
            output_path=self.output,
        )

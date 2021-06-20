import inspect
import os
from pathlib import Path

from loguru import logger

import reprobench
from reprobench.tools.executable import ExecutableTool


class PrefExec(ExecutableTool):
    name = "MC Preprocessor"
    path = ""

    # path="./satmod_wrapper.sh"

    def __init__(self, context):
        super().__init__(context)
        self.output = self.parameters.get('output')

    def get_arguments(self):
        return [f"{self.prefix}{key} {value}" for key, value in self.parameters.items()]

    def get_cmdline(self):
        logger.warning(self.get_path())
        logger.trace(self.get_arguments())
        tmpdir = self.parameters['exec_tmpdir'].format(**self.parameters,
                                                       run="{run}", filename="{filename}")
        #set all parameters as attributes
        for key in self.parameters:
            setattr(self, key, self.parameters[key])

        self.tmpdir = tmpdir
        self.delete_tmp = self.parameters.get('delete_tmp', True)
        cmd = self.parameters['cmd'].format(**self.parameters)
        logger.warning(f"CMD is {cmd}")
        # raise RuntimeError
        return [cmd]

    def run(self, executor):
        my_env = os.environ.copy()
        self.run_internal(executor, my_env)

    def run_internal(self, executor, environment):
        logger.debug([*self.get_cmdline(), self.task])

        executor.run(
            self.get_cmdline(),
            directory=self.cwd,
            input_str="%s" % self.task,
            out_path=self.get_out_path(),
            err_path=self.get_err_path(),
            output_path=self.output,
            tmpdir=self.tmpdir,
            delete_tmp=self.delete_tmp,
        )

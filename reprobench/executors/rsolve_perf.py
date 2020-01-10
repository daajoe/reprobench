import os
from subprocess import Popen, PIPE
import re
from loguru import logger
import json

import reprobench
from reprobench.utils import send_event
from .base import Executor
from .db import RunStatistic, RunStatisticExtended
from .events import STORE_RUNSTATS, STORE_THP_RUNSTATS

runsolver_re = {
    "SEGFAULT": re.compile(r"^\s*Child\s*ended\s*because\s*it\s*received\s*signal\s*11\s*\((?P<val>SIGSEGV)\)\s*"),
    "STATUS": re.compile(r"Child status: (?P<val>[0-9]+)"),
}


perf_re = {
    "tlb_miss": re.compile(r"\s*(?P<val>[0-9]+(\.[0-9]+)?)\s*dTLB-load-misses\s*"),
    "cycles": re.compile(r"\s*(?P<val>[0-9]+(\.[0-9]+)?)\s*cycles\s*"),
    "stall_cycles": re.compile(r"\s*(?P<val>[0-9]+(\.[0-9]+)?)\s*stalled-cycles-backend\s*"),
    "cache_misses": re.compile(r"\s*(?P<val>[0-9]+(\.[0-9]+)?)\s*cache-misses\s*"),
    "elapsed": re.compile(r"\s*(?P<val>[0-9]+(\.[0-9]+)?)\s*seconds time elapsed\s*"),
    "cpu_migrations": re.compile(r"\s*(?P<val>[0-9]+(\.[0-9]+)?)\s*cpu-migrations\s*"),
    "page_faults": re.compile(r"\s*(?P<val>[0-9]+)\s*page-faults\s*"),
    "context_switches": re.compile(r"\s*context-switches\s*"),
}

class RunSolverPerfEval(Executor):
    def __init__(self, context, config):
        self.socket = context["socket"]
        self.run_id = context["run"]["id"]

        if config is None:
            config = {}

        wall_grace = config.get("wall_grace", 15)
        self.nonzero_as_rte = config.get("nonzero_rte", True)

        limits = context["run"]["limits"]
        time_limit = float(limits["time"])
        MB = 1

        self.wall_limit = time_limit + wall_grace
        self.cpu_limit = time_limit
        self.mem_limit = float(limits["memory"]) * MB
        self.reprobench_path = os.path.abspath(os.path.join(os.path.dirname(reprobench.__file__),'..'))


    @staticmethod
    def perf_parse_from_file(perflog):
        with codecs.open(perflog, errors='ignore', encoding='utf-8') as f:
            perf_parse(f.readlines())

    @staticmethod
    def perf_parse(string):
        perf_res = {}
        for line in string:
            for val, reg in perf_re.items():
                m = reg.match(line)
                if m: perf_res[val] = m.group("val")
        return stats

    @classmethod
    def register(cls, config=None):
        RunStatisticExtended.create_table()


    @staticmethod
    def compile_stats(stats, run_id, nonzero_as_rte):
        try:
            stats['return_code'] = stats['runsolver_STATUS']
        except KeyError:
            stats['return_code'] = '9'
        stats['cpu_time'] = stats['runsolver_CPUTIME']
        stats['wall_time'] = stats['runsolver_WCTIME']
        stats['max_memory'] = stats['runsolver_MAXVM']

        logger.error(stats)

        if stats["runsolver_TIMEOUT"] == 'true':
            verdict = RunStatisticExtended.TIMEOUT
        elif stats["runsolver_MEMOUT"] == 'true':
            verdict = RunStatisticExtended.MEMOUT
        elif ("error" in stats and stats["error"] != '') or \
            (nonzero_as_rte and nonzero_as_rte.lower() == 'true' and int(stats['return_code']) != 0):
            verdict = RunStatisticExtended.RUNTIME_ERR
        else:
            verdict = RunStatisticExtended.SUCCESS

        if 'error' in stats:
            del stats["error"]
        if 'runsolver_STATUS' not in stats:
            stats['runsolver_STATUS'] = 1

        stats['run_id'] = run_id
        stats['verdict'] = verdict

        logger.trace(stats)
        return stats

    def run(
        self,
        cmdline,
        out_path=None,
        err_path=None,
        input_str=None,
        directory=None,
        **kwargs,
    ):

        #TODO: fix out_path
        outdir = os.path.abspath(os.path.join(self.reprobench_path,os.path.dirname(out_path)))
        payload_p, perflog, stderr_p, stdout_p, varfile, watcher, runparameters_p = self.log_paths(outdir)

        logger.debug(perflog)

        solver_cmd = "%s %s" %(' '.join(cmdline), input_str)

        perfcmdline = "/usr/bin/perf stat -o %s -e dTLB-load-misses,cycles,stalled-cycles-backend,cache-misses %s" % (
        perflog, solver_cmd)
        runsolver = os.path.expanduser("~/bin/runsolver")
        run_cmd = f"{runsolver:s} --vsize-limit {self.mem_limit:.0f} -W {self.cpu_limit:.0f}  -w {watcher:s} -v {varfile:s} {perfcmdline:s} > {stdout_p:s} 2>> {stderr_p:s}"

        logger.trace('Logging run parameters to %s' %runparameters_p)
        with open(runparameters_p, 'w') as runparameters_f:
            run_details = {'run_id': self.run_id}
            runparameters_f.write(json.dumps(run_details))

        logger.debug(run_cmd)
        logger.debug(f"Running {directory}")
        p_solver = Popen(run_cmd, stdout=PIPE, stderr=PIPE, shell=True, close_fds=True, cwd=outdir)
        output, err = p_solver.communicate()

        stats = {}
        if err != b'':
            logger.error(err)
            stats['error'] = err
        else:
            stats['error'] = ''

        stats = self.parse_logs(perflog, varfile, watcher, stats)

        logger.trace(stats)
        logger.debug(f"Finished {directory}")

        payload = self.compile_stats(stats, self.run_id, self.nonzero_as_rte)

        logger.error(payload)
        with open(payload_p, 'w') as payload_f:
            payload_f.write(json.dumps(payload))

        # send_event(self.socket, STORE_RUNSTATS, payload)
        send_event(self.socket, STORE_THP_RUNSTATS, payload)

    @staticmethod
    def log_paths(outdir):
        stdout_p = '%s/stdout.txt' % (outdir)
        stderr_p = '%s/stderr.txt' % (outdir)
        watcher = '%s/watcher.txt' % (outdir)
        varfile = '%s/varfile.txt' % (outdir)
        perflog = '%s/perflog.txt' % (outdir)
        payload_p = '%s/result.json' % (outdir)
        runparameters_p = '%s/run.json' % (outdir)
        return payload_p, perflog, stderr_p, stdout_p, varfile, watcher, runparameters_p

    @staticmethod
    def parse_logs(perflog, varfile, watcher, stats=None):
        if stats is None:
            stats={}
        # runsolver parser
        with open(f"{varfile:s}") as f:
            for line in f:
                # TODO: debuglevel
                # logger.debug(line)
                if line.startswith('#') or len(line) == 0:
                    continue
                line = line[:-1].split("=")
                stats['runsolver_%s' % line[0]] = line[1]
        logger.trace(stats)
        # runsolver watcher parser (returncode etc)
        # for line in codecs.open(perflog, errors='ignore', encoding='utf-8'):
        with open(f"{watcher:s}") as f:
            for line in f.readlines():
                # TODO: debuglevel
                # logger.debug(line)
                for val, reg in runsolver_re.items():
                    m = reg.match(line)
                    if m: stats['runsolver_%s' % val] = m.group("val")
        logger.trace(stats)
        # perf result parser
        with open(f"{perflog:s}") as f:
            for line in f.readlines():
                # logger.debug(line)
                for val, reg in perf_re.items():
                    m = reg.match(line)
                    if m: stats['perf_%s' % val] = m.group("val")
        return stats
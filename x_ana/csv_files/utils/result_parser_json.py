#!/usr/bin/env python3
import glob
import json
import os
import pathlib
import re
from unqlite import UnQLite
from loguru import logger
import numpy as np

# runsolver VAR file
var_patterns = {"RETCODE": "return_code", "SIGNAL": "signal", "WCTIME": "wall_time",
                "TIMEOUT": "timeout", 'MEMOUT': "memout", 'MAXVM': 'max_memory',
                'CPUTIME': 'cpu_time', 'SYSTEMTIME': 'cpu_sys_time'}

# solver stderr parsing patterns
solver_stderr_re = {
}

# solver stdout parsing patterns
solver_re = {
    # s SATISFIABLE
    # c type mc
    # c s log10-estimate 0.3010299956639812
    # c s exact quadruple int 2
    "mc": {
        "count_old": (re.compile(r"s\s*mc\s*(?P<val>([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?))"), lambda x: x),
        "decision": (re.compile(r"^s\s+(?P<val>(UNSATISFIABLE|SATISFIABLE|UNKNOWN))"), lambda x: x),
        "type": (re.compile(r"^(?P<val>!SAT)"), lambda x: x),
        "log10_est": (re.compile(r"^c\s+s\s+log10-estimate\s+(?P<val>([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?))"),
                      lambda x: x),
        "count": (re.compile(r"^c\s+s\s+(approx|exact)\s+(arb|single|double|quadruple)\s+"
                              r"(int|log10|prec-sci|float)\s+"
                              r"(?P<val>([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?))"), lambda x: x),
    },
}

solver_name_re = re.compile(r"(bash|python)\[solver=(?P<solver>([\w.\-]*))(?P<group>(,([\w=]*))*)\]")
rss_re = re.compile(r"default\[s=[\w.-]+(,[\w.-]+)*(,rss=(?P<rss>(\w*)))?(,[\w*]=[\w.-]+)*\]")


def extract_result_solver(stream, solver, d, sre):
    if solver not in sre:
        return
    for line in stream.readlines():
        for val, reg in sre[solver].items():
            m = reg[0].match(line)
            if m:
                key = f'{val}'
                d[key] = sre[solver][val][1](m.group('val'))
    return solver


def extract_data(stream, d, delimn, patterns):
    for line in stream.readlines():
        for p, k in patterns.items():
            n = line.find(p)
            if n != -1:
                m = line.rfind(delimn)
                if m == -1:
                    continue
                if delimn == ":":
                    d[k] = float(line[m + 2:])
                elif delimn == "=":
                    try:
                        d[k] = float(line[m + 1:])
                    except ValueError:
                        d[k] = line[m + 1:-1]
                else:
                    raise NotImplementedError


def fix_jsons(folder, db, from_json=True, from_varfile=True, platform='missing',
              hostname='missing', rss_default='nan', run_id_prefix='output/sat_arch'):
    solver_rexex = re.compile(solver_name_re)
    writeout = True
    i = 0
    if writeout:
        if pathlib.Path(db).exists():
            pathlib.Path(db).unlink()
        db = UnQLite(db)
        collection = db.collection('data')
        if not collection.exists():
            collection.create()  # Create the collection.

    for file in glob.glob(folder, recursive=True):
        # print(file)
        dirname = os.path.dirname(file)
        decode = True
        if from_json:
            try:
                with open(f"{dirname}/result.json", "r") as fh:
                    d = json.load(fh)
            except json.decoder.JSONDecodeError:
                decode = False
                from_json = False
                from_varfile = True
            d['rss'] = rss_default
            if hostname != 'missing':
                d['hostname'] = hostname
        if not from_json or not decode:
            short_dirname = dirname[dirname.find('default'):]
            d = {"run_id": f"{run_id_prefix}/{short_dirname}", "wall_time": "nan", "cpu_sys_time": "nan",
                 "cpu_time": "nan",
                 "platform": platform, "hostname": hostname, "verdict": "RTE",
                 "return_code": 64, "signal": 0, "runsolver_STATUS": 64, "runsolver_TIMEOUT": 0,
                 "runsolver_MEMOUT": 0, "max_memory": "nan", "rss": rss_default}

        try:
            m=solver_rexex.match(d['run_id'].split('/')[2])
            if m:
                solver=m.group('solver')
            else:
                solver=f"NA"
                logger.error(f"Could not determine solver for run_id: {d['run_id']}")
            d['solver'] = solver
            d['instance'] = '/'.join(d['run_id'].split('/')[3:-1])
            d['run'] = int(d['run_id'].split('/')[-1])
            d['count'] = np.nan
            d['log10_est'] = np.nan
            d['penalty'] = np.nan
            d['depr'] = np.nan
        except IndexError:
            logger.warning(d['run_id'])
            raise RuntimeError
        rss = re.findall(rss_re, d['run_id'].split('/')[2])
        if rss and rss != [('', '', '', '', '')]:
            if rss[0][2] != '':
                d['rss'] = f"z%sG" %rss[0][2]

        with open(f"{dirname}/stdout.txt", "r") as fh:
            extract_result_solver(stream=fh, solver="mc", d=d, sre=solver_re)
        # parse the runsolver varfile if we want to run a clean parsing
        if not from_json:
            try:
                with open(f"{dirname}/varfile.txt", 'r') as var_p:
                    extract_data(stream=var_p, d=d, delimn="=", patterns=var_patterns)
                    if 'timeout' in d:
                        if (d['timeout'] == 'true' or d['timeout'] == '1'):
                            d['verdict'] = 'TLE'
                        del d['timeout']
                    if 'memout' in d:
                        if (d['memout'] == 'true' or d['memout'] == '1'):
                            d['verdict'] = 'MEM'
                        del d['memout']
            except FileNotFoundError as e:
                logger.error(f'Runsolver Error on instance "{dirname}".')
                d['verdict'] = "ENV"
        else:
            try:
                d['cpu_sys_time'] = d['runsolver_SYSTEMTIME']
            except KeyError:
                pass

        d['penalty'] = 0
        if not 'decision' in d:
            d['depr'] = 1
            if 'count_old' in d:
                d['desc'] = 'UNSATISFIABLE' if d['count_old'] == '0' else "SATISFIABLE"
                d['count'] = d['count_old']
            else:
                d['desc'] = "UNKNOWN"
                d['count'] = np.nan
        else:
            d['depr'] = 0
            d['desc'] = d['decision']
            del d['decision']

        if d['desc'] == 'UNKNOWN':
            d['count'] = np.nan
        if d['desc'] in ("SATISFIABLE", "UNSATISFIABLE") and not 'count' in d:
            d['penalty']=1
            d['desc']='UNKNOWN'
            d['count']=np.nan

        if not d['desc']  in ("UNKNOWN", "SATISFIABLE", "UNSATISFIABLE"):
            print(dirname)
            print(d['return_code'])
            print(d)
            raise NotImplementedError
            # MEMOUT = "MEM"
            # RUNTIME_ERR = "RTE"
            # OUTPUT_LIMIT = "OLE"
        with open(f"{dirname}/result.json", "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=4)

        # print(d)
        # exit(2)

        if writeout:
            collection.store(d)

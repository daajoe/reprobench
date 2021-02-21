#!/usr/bin/env python3
import glob
import json
import os
import pathlib

import pandas as pd
from loguru import logger
from unqlite import UnQLite

df = None
# from x_ana.utils import keys
keys = [
    'solver', 'run', 'instance',
    'platform', 'hostname',
    'return_code', 'cpu_time', 'wall_time', 'max_memory', 'verdict',
    'run_id', 'rss', 'cpu_sys_time', 'desc', 'depr', 'count'
]

def data2csv(source, output, unqlite):
    df = pd.DataFrame(columns=keys)
    if unqlite:
        if not pathlib.Path(source).exists():
            raise RuntimeError
        db = UnQLite(source)
        collection = db.collection('data')
        if not collection.exists():
            raise RuntimeError

        i = 0

        for d in collection.all():
            if i % 500 == 0:
                logger.info(i)
            i += 1

            for k in set(d.keys()) - set(keys):
                del d[k]

            # print(d)
            df.loc[len(df)] = d
    else:
        for file in glob.glob(source, recursive=True):
            json_filename = f"{os.path.dirname(file)}/result.json"
            with open(json_filename, "r") as fh:
                d = json.load(fh)

            for k in set(d.keys()) - set(keys):
                del d[k]

            df.loc[len(df)] = d

    # print(df[df.run_id.str.contains('SAT_dat.k85.debugged.cnf') & df.run_id.str.contains('glucose')])

    logger.info(f"Write {output}")
    df.to_csv(f'{output}')

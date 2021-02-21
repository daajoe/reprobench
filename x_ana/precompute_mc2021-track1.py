#!/usr/bin/env python
import os
import re
from decimal import Decimal
from functools import reduce

import gmpy2
import numpy as np
import pandas as pd
from gmpy2 import xmpz, mpz, mpfr, digits, num_digits, frexp, ieee, exp10, get_exp, f2q
from mpmath import mp, fp, nstr, matrix
from pandas.plotting import scatter_matrix
from unqlite import UnQLite

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('max_colwidth', 400)
# pd.options.mode.chained_assignment = 'warn'

import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt

outf = "1-outputs_track1"

if not os.path.exists(f"{outf}"):
    os.makedirs(f"{outf}")


def x(L):
    return reduce(lambda x, y: x + y, L.values())


for filename in ['csv_files/output_sat_haswell.csv']:
    print('=' * 200)
    print(filename)
    print('=' * 200)
    df = pd.read_csv(filename, index_col=0)
    filename = os.path.basename(filename)


    # SET RUNTIME LIMIT
    df.loc[df.wall_time > 1800, 'verdict'] = "TLE"

    df.loc[df.verdict == "MEM", 'wall_time'] = np.nan
    df.loc[df.verdict == "RTE", 'wall_time'] = np.nan
    df.loc[df.verdict == "TLE", 'wall_time'] = np.nan

    # We have no counts
    df.loc[(df.verdict == "OK") & (df['count'] == '0'), 'verdict'] = 'RTE'
    df.loc[(df['count'] == '0'), 'count'] = np.nan

    # Restricting run to 0 only
    df = df[df.run == 0]
    df = df[['run_id', 'instance', 'solver', 'verdict', 'return_code', 'wall_time', 'count']]
    df.sort_values(by=['instance'], inplace=True)
    df.to_csv(f'{outf}/{filename}.csv')

    # quick overview on solved instances etc...
    z = df.groupby(['verdict', 'solver']).agg(
        {'wall_time': [np.sum, 'count', np.mean]})

    z.to_csv(f'{outf}/{filename}_overview_unvalidated.csv')

    # --------------------------------------------------------------------------------------------
    # Instance / Solver (MEM/TO/TLE Info)
    # --------------------------------------------------------------------------------------------
    to_info = df.copy()

    to_info.wall_time = to_info.wall_time.round(2)
    to_info.loc[df.verdict == "MEM", 'wall_time'] = "MEM"
    to_info.loc[df.verdict == "RTE", 'wall_time'] = "RTE"
    to_info.loc[df.verdict == "TLE", 'wall_time'] = "TLE"

    solvers = to_info['solver'].unique()
    to_collect = to_info[['instance']].reset_index(drop=True).drop_duplicates().reset_index(drop=True)

    for solver in solvers:
        solver_df = to_info[(to_info['solver'] == solver)]  # .copy()
        to_collect = pd.merge(to_collect, solver_df[['instance', 'wall_time']], on=['instance'], how='outer')
        to_collect.rename(columns={'wall_time': solver}, inplace=True)

    to_collect.to_csv(f'{outf}/{filename}_wall_comp_details_unvalidated.csv', float_format='%.2f')


#!/usr/bin/env python3
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

outf = "1-precomp_track1"

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

    #RESET UNKNOWN INSTANCES
    df.loc[df.verdict != "OK", 'wall_time'] = np.nan
    df.loc[df.verdict != "OK", 'count'] = np.nan
    df.loc[df.log10_est == 0, 'log10_est'] = np.nan

    # ALL COUNTS
    df[['instance','solver','log10_est','verdict']].\
        sort_values(by=['instance','solver']).to_csv(f'{outf}/counts-log10_ests.csv',index=False)
    solvers=df['solver'].unique()
    inst_overview = df[['instance']].drop_duplicates()
    for solver in solvers:
        x=df[df.solver==solver][['instance','log10_est']]
        inst_overview = pd.merge(inst_overview, x[['instance', 'log10_est']], on=['instance'], how='outer')
        inst_overview.rename(columns={'log10_est': solver}, inplace=True)
    inst_overview.sort_values(by=['instance']).\
        to_csv(f'{outf}/{filename}-log10_overview.csv', index=False,float_format='%.9f')

    df = df[['run_id', 'instance', 'solver', 'verdict', 'return_code', 'wall_time', 'count']]
    df.sort_values(by=['instance'], inplace=True)
    df.to_csv(f'{outf}/{filename}.csv')


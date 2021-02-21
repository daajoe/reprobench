#!/usr/bin/env python3

from x_ana.csv_files.utils.result_parser_json import *
fix_jsons("../outputs/output/**/stdout.txt", 'output_haswell64.unqlite', rss_default='1G', hostname='taurus-haswell')

from x_ana.csv_files.utils.unqlite2csv import *
data2csv('output_haswell64.unqlite', 'output_sat_haswell.csv', unqlite=True)

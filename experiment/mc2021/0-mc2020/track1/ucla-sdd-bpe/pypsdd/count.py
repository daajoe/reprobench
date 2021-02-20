#!/usr/bin/env python2
from __future__ import print_function
import sys
from pypsdd import Vtree,SddManager
from pypsdd import io

sdd_filename = sys.argv[1]
vtree_filename = sys.argv[2]


vtree = Vtree.read(vtree_filename)
manager = SddManager(vtree)
alpha = io.sdd_read(sdd_filename,manager)
mc = alpha.model_count(vtree)
print("%d" % mc)

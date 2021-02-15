#!/bin/bash

set -e

ulimit -t 60

TMP_BASENAME="tmp/ucla"
TMP_CNF="${TMP_BASENAME}.cnf"
TMP_BPE_CNF="${TMP_BASENAME}_bpe.cnf"
BPE_EXE="bin/B+E_linux"

$BPE_EXE $TMP_CNF &> $TMP_BPE_CNF # ACACAC

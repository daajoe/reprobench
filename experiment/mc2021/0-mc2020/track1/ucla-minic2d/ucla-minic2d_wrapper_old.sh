#!/bin/bash

set -e
BIN_DIR=$(realpath $(dirname $0))

TMP_BASENAME="tmp/ucla"
TMP_CNF="${TMP_BASENAME}.cnf"
TMP_LOG="${TMP_BASENAME}.log"
EXE="bin/miniC2D"

mkdir -p tmp
cat > $TMP_CNF
$BIN_DIR/$EXE --cnf $TMP_CNF --count_models > $TMP_LOG
OUTPUT=$(grep "Counting" $TMP_LOG)
MC=$(python -c "print('${OUTPUT}'.strip().split(' ')[1])")
echo "s mc ${MC//,}"


# USE PYTHON NNF EVALUATOR


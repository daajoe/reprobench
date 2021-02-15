#!/bin/bash

set -e

BIN_DIR=$(realpath $(dirname $0))

TMP_BASENAME="tmp/ucla"
TMP_CNF="${TMP_BASENAME}.cnf"
TMP_BPE_CNF="${TMP_BASENAME}_bpe.cnf"
TMP_SDD="${TMP_BASENAME}.sdd"
TMP_VTREE="${TMP_BASENAME}.vtree"
TMP_LOG="${TMP_BASENAME}.log"
EXE="bin/sdd-linux"
BPE_EXE="bin/B+E_linux"
BPE_SCRIPT="./runbpe.bash"

mkdir -p tmp
cat > $TMP_CNF

if $BIN_DIR/$BPE_SCRIPT; then
    HEADER=$(grep "^p" $TMP_BPE_CNF) || true
    if [ -z "$HEADER" ]; then
        echo "s mc 0"
        exit
    fi
    VAR_COUNT=$(python -c "print('${HEADER}'.strip().split()[-2])")
    CLAUSE_COUNT=$(python -c "print('${HEADER}'.strip().split()[-1])")
    if [ "$CLAUSE_COUNT" == "0" ]; then
        echo "s mc $((2 ** $VAR_COUNT))"
        exit
    fi
    $BIN_DIR/$EXE -c $TMP_BPE_CNF -R $TMP_SDD -W $TMP_VTREE > $TMP_LOG
else
    $BIN_DIR/$EXE -c $TMP_CNF -R $TMP_SDD -W $TMP_VTREE > $TMP_LOG
fi

OUTPUT=$(grep "sdd model count" $TMP_LOG)
MC=$(python -c "print('${OUTPUT}'.split(':')[1].strip().split(' ')[0])")
#echo "s mc ${MC//,}"
$BIN_DIR/pypsdd/count.py

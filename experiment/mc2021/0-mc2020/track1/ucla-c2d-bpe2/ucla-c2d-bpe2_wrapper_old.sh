#!/bin/bash

set -e

BIN_DIR=$(realpath $(dirname $0))

TMP_BASENAME="tmp/ucla"
TMP_CNF="${TMP_BASENAME}.cnf"
TMP_BPE_CNF="${TMP_BASENAME}_bpe.cnf"
TMP_LOG="${TMP_BASENAME}.log"
EXE="bin/c2d"
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
    $BIN_DIR/$EXE -in $TMP_BPE_CNF -count > $TMP_LOG
else
    $BIN_DIR/$EXE -in $TMP_CNF -count > $TMP_LOG
fi

OUTPUT=$(grep "Counting" $TMP_LOG)
MC=$(python -c "print('${OUTPUT}'.strip('Counting.').split(' ')[0])")
echo "s mc ${MC//,}"

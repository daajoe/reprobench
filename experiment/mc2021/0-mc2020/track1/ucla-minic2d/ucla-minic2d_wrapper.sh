#!/usr/bin/env bash
#set -x
# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

echo "c o CALLSTR $*"

for i in "$@"
do
case $i in
    -t=*|--tmpdir=*)
    PTMPDIR="${i#*=}"
    shift # past argument=value
    ;;
    -r=*|--maxrss=*)
    PMAXRSS="${i#*=}"
    shift # past argument=value
    ;;
    -d=*|--maxtmp=*)
    PMAXTMP="${i#*=}"
    shift # past argument=value
    ;;
    -w=*|--timeout=*)
    PTIMEOUT="${i#*=}"
    shift # past argument=value
    ;;
    -a=*|--task=*)
    PTASK="${i#*=}"
    shift # past argument=value
    ;;
    --default)
    DEFAULT=YES
    shift # past argument with no value
    ;;
    *)
          # unknown option
    ;;
esac
done
shift $((OPTIND))

echo "c o =============== TEST CMDLINE ARGS ========================="
echo "c o CMDLINE TMPDIR = ${PTMPDIR}"
echo "c o CMDLINE PMAXTMP = ${PMAXTMP}"
echo "c o CMDLINE MAXRSS = ${PMAXRSS}"
echo "c o CMDLINE TIMEOUT = ${PTIMEOUT}"

echo "c o =============== TEST ENV VARS ==========================="
echo "c o ENV TMPDIR = ${TMPDIR}"
echo "c o ENV PMAXTMP = ${MAXTMP}"
echo "c o ENV MAXRSS = ${MAXRSS}"
echo "c o ENV TIMEOUT = ${TIMEOUT}"

echo "c o ================= SET PRIM INTRT HANDLING ==============="
function interrupted(){
  echo "c o Sending kill to subprocess"
  kill -TERM $PID
  echo "c o Removing tmp files"
  [ ! -z "$TMP_CNF" ] && rm TMP_CNF
  [ ! -z "$TMP_BPE_CNF" ] && rm $TMP_BPE_CNF
  [ ! -z "$TMP_LOG" ] && rm $TMP_LOG
}

function finish {
  # Your cleanup code here
  echo "c o Removing tmp files"
  [ ! -z "$TMP_CNF" ] && rm TMP_CNF
  [ ! -z "$TMP_BPE_CNF" ] && rm $TMP_BPE_CNF
  [ ! -z "$TMP_LOG" ] && rm $TMP_LOG
}
trap finish EXIT
trap interrupted TERM
trap interrupted INT

echo "c o ================= POS CMDLINE ARGS ==============="
echo "c o $*"

echo "c o ================= Changing directory to output directory ==============="
cd "$(dirname "$TMPDIR")" || (echo "Could not change directory to $TMPDIR. Exiting..."; exit 1)

TMP_CNF=$(mktemp ${PTMPDIR}/XXXXXX.cnf)
TMP_BPE_CNF=$(mktemp ${PTMPDIR}/XXXXXX_bpe.cnf)
TMP_LOG=$(mktemp ${PTMPDIR}/XXXXXX.log)
# ============================================================
# Commands
BIN_DIR=$(realpath $(dirname $0)/bin)
EXE="${BIN_DIR}/miniC2D"
BPE_EXE="${BIN_DIR}/B+E_linux"

echo "c o ================= RUNNING B+E ==============="
myenv="TMPDIR=$1"
cmd="$EXE --count_models --cnf $TMP_BPE_CNF"
echo "c o SOLVERCMD=$cmd"

env $myenv $cmd > $TMP_LOG &
PID=$!
wait $PID
exit_code=$?
echo "c solver_wrapper: ==============================="
echo "c solver_wrapper: Solver finished with exit code="$exit_code
echo "c f RET="$exit_code

if ! [ $exit_code -eq "0" ] ; then
  echo "s UNKNOWN"
  exit 1
fi


OUTPUT=$(grep "Counting" $TMP_LOG)
result=$(python3 -c "print('${OUTPUT}'.split(' ')[3]);")


if [ $result -eq "0" ] ; then
  echo "s UNSATISFIABLE"
  echo "c s type $PTASK"
  echo "c s log10-estimate inf"
  echo "c s exact quadruple int 0"
else
  echo "s SATISFIABLE"
  echo "c type $PTASK"
  #let's play codegolf
  log10=$(echo $result | python3 -c 'import sys; import math; print(math.log10(int(sys.stdin.readline())));')
  echo "c s log10-estimate $log10"
  echo "c s exact quadruple int $result"
fi

exit $exit_code

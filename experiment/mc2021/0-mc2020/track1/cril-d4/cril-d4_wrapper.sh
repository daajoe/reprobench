#!/usr/bin/env bash
#set -x
# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

echo "c o CALLSTR $@"

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
  [ ! -z "$prec_tmpfile" ] && rm prec_tmpfile
  [ ! -z "$tmpfile" ] && rm $tmpfile
}
function finish {
  # Your cleanup code here
  echo "c o Removing tmp files"
  [ ! -z "$prec_tmpfile" ] && rm prec_tmpfile
  [ ! -z "$tmpfile" ] && rm $tmpfile
}
trap finish EXIT
trap interrupted TERM
trap interrupted INT

echo "c o ================= POS CMDLINE ARGS ==============="
echo "c o $@"

echo "c o ================= Changing directory to output directory ==============="
cd "$(dirname "$0")" || (echo "Could not change directory to $0. Exiting..."; exit 1)

BIN_DIR=$(realpath $(dirname $0))

echo "c o ================= Preparing tmpfiles ==============="
prec_tmpfile=$(mktemp ${PTMPDIR}/result.XXXXXX)
tmpfile=$(mktemp ${PTMPDIR}/result.XXXXXX)

echo "c o ================= Running Preprocessor ==============="
preproc_cmd=$BIN_DIR"/BiPe -preproc $1"
echo "c o PRE=$preproc_cmd"
# you asked for for c t mc instead of the suggested ct mc
# so bugfixing the c t mc problem with some solvers;
sed -i '/^c t/d' $1

$preproc_cmd > $prec_tmpfile &
PID=$!
wait $PID
exit_code=$?

if [ $exit_code -eq "0" ] ; then
  echo "c o ================= Preprocessor Successful ==============="
  filename=$prec_tmpfile
else
  echo "c o ================= Preprocessor Failed using input file ==============="
  filename=$1
fi

echo "c o ================= Running Solver ==============="
cmd="$BIN_DIR/d4 -$PTASK $filename"
myenv="TMPDIR=$TMPDIR"
echo "c o SOLVERCMD=$cmd"

env $myenv $cmd > $tmpfile &
PID=$!
wait $PID
exit_code=$?
echo "c solver_wrapper: ==============================="
echo "c solver_wrapper: Solver finished with exit code="$exit_code
echo "c f RET="$exit_code

result=$(cat $tmpfile | grep "^s " | awk '{print $2}')
if [ $result -eq "0" ] ; then
  echo "s UNSATISFIABLE"
  echo "c s $PTASK"
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

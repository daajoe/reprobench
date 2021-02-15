#!/usr/bin/env bash

# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
#verbose=0
thp=0
preprocessor="none"
while getopts "h?vt:s:f:i:d:" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    v)  echo "Currently unsupported."
        #verbose=1
        ;;
    t)  thp=$OPTARG
        ;;
    s)  solver=$OPTARG
        ;;
    f)  filename=$OPTARG
        ;;
    i)  original_input=$OPTARG
        ;;
    d)  dir=$OPTARG
	;;
    esac
done

shift $((OPTIND-1))

function interrupted(){
  kill -TERM $PID
}
trap interrupted TERM
trap interrupted INT


if [ -z "$solver" ] ; then
  echo "No Solver given. Exiting..."
  exit 1
fi

if [ -z "$filename" ] ; then
  echo "No filename given. Exiting..."
  exit 1
fi

if [ ! -f "$filename" ] ; then
  echo "Filename does not exist. Exiting..."
  exit 1
fi

if [ "$thp" == 1 ] ; then
  env=GLIBC_THP_ALWAYS=1
else
  env=VOID=1
fi

cd "$(dirname "$0")" || (echo "Could not change directory to $0. Exiting..."; exit 1)


if [ "$solver" == "approxmc" ] ; then
    solver_cmd="./approxmc_glibc $*"
elif [ "$solver" == "c2d" ] ; then
    solver_cmd="./c2d $* -count -in_memory -smooth_all -in "
elif [ "$solver" == "cachet" ] ; then
    solver_cmd="./cachet_glibc $*"
elif [ "$solver" == "d4" ] ; then
    solver_cmd="./d4 $*"
elif [ "$solver" == "ganak" ] ; then
    solver_cmd="./ganak_glibc -p $*"
elif [ "$solver" == "minic2d" ] ; then
    solver_cmd="./minic2d_glibc -C $* -c"
elif [ "$solver" == "sharpsat" ] ; then
    solver_cmd="./sharpsat_glibc $*"
elif [ "$solver" == "addmc" ] ; then
    solver_cmd="./ADDMC/addmc $*"
elif [ "$solver" == "art-ai" ] ; then
    solver_cmd="./art-ai/sdd-solver $*"
elif [ "$solver" == "compile" ] ; then
    solver_cmd="./compile/compile_team.sh -m $filename $*"
elif [ "$solver" == "count_bareganak" ] ; then
    solver_cmd="./count_bareganak/count_noproj_bareganak $*"
elif [ "$solver" == "ispence" ] ; then
    solver_cmd="./ispence/SUMC1 $*"
elif [ "$solver" == "msoos" ] ; then
    solver_cmd="./msoos/count_noproj $*"
elif [ "$solver" == "nus-narasimha" ] ; then
    solver_cmd="./nus-narasimha/count_noprojaccurate $*"
elif [ "$solver" == "nus-onlyapprox" ] ; then
    solver_cmd="./nus-onlyapprox/count_noprojaccurate $*"
elif [ "$solver" == "swats" ] ; then
    solver_cmd="./swats/swats $*"
elif [ "$solver" == "ucla-c2d" ] ; then
    solver_cmd="./ucla-c2d/c2d-solver $*"
elif [ "$solver" == "ucla-c2d-bpe" ] ; then
    solver_cmd="./ucla-c2d-bpe/c2d-bpe-solver $*"
elif [ "$solver" == "ucla-c2d-bpe2" ] ; then
    solver_cmd="./ucla-c2d-bpe2/c2d-bpe-solver $*"
elif [ "$solver" == "ucla-minic2d" ] ; then
    solver_cmd="./ucla-minic2d/minic2d-solver $*"
elif [ "$solver" == "ucla-minic2d-bpe" ] ; then
    solver_cmd="./ucla-minic2d-bpe/minic2d-bpe-solver $*"
elif [ "$solver" == "ucla-sdd-bpe" ] ; then
    solver_cmd="./ucla-sdd-bpe/sdd-bpe-solver $*"
elif [ "$solver" == "c2d-mc-solver" ] ; then
    solver_cmd="./c2d-mc-solver/c2d-solver $*"
elif [ "$solver" == "MCSim" ] ; then
    solver_cmd="./MCSim/MCSim.sh $*"
else
  solver_cmd="./"$solver" $*"
fi


cd $dir
solver_cmd=/mnt/vg01/lv01/home/decodyn/reprobench/experiment/mcc2020/tool/mc/bins/$solver_cmd

echo "c Original input instance was $original_input"
echo "c Running from directory $dir"
echo "c env $env $solver_cmd $filename"
echo "c "

#NOTE: if you need to redirect the solver output in the future, we suggest to use stdlog.txt
#
# run call in background and wait for finishing
env $env $solver_cmd < $filename &
#alternative approach
#(export $env; $solver_cmd $filename) &
PID=$!
wait $PID
exit_code=$?
echo "c Solver finished with exit code="$exit_code
exit $exit_code

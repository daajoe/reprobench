#!/usr/bin/env bash

# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
#verbose=0
while getopts "h?vt:s:f:i:d:" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    v)  echo "Currently unsupported."
        #verbose=1
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


cd "$(dirname "$0")" || (echo "Could not change directory to $0. Exiting..."; exit 1)


echo "$@"



env "$@" &
#env $env $solver_cmd $filename &
PID=$!
wait $PID
exit_code=$?
echo "c solver_wrapper: ==============================="
echo "c solver_wrapper: Solver finished with exit code="$exit_code
echo "f RET="$exit_code

exit $exit_code

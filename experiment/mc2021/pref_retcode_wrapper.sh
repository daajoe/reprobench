#!/usr/bin/env bash

function interrupted(){
  kill -TERM $PID
}
trap interrupted TERM
trap interrupted INT


cd "$(dirname "$0")" || (echo "Could not change directory to $0. Exiting..."; exit 1)
#
env "$@" &
#env $env $solver_cmd $filename &
PID=$!
wait $PID
exit_code=$?
echo "c solver_wrapper: ==============================="
echo "c solver_wrapper: Solver finished with exit code="$exit_code
echo "f RET="$exit_code

exit $exit_code

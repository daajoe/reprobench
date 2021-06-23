#!/usr/bin/env bash

function interrupted(){
  kill -TERM $PID
}
trap interrupted TERM
trap interrupted INT

cd "$(dirname "$0")" || (echo "Could not change directory to $0. Exiting..."; exit 1)

echo "Activating conda environment"
CONDA_PATH=$(conda info | grep -i 'base environment' | awk '{print $4}')
source $CONDA_PATH/etc/profile.d/conda.sh
conda activate satmod
echo "Parameters are $@"

which python3
#TODO: fix on cluster
env /home/jfichte/anaconda3/envs/satmod/bin/python3 /home/jfichte/satmod/wormos/slorw.py "$@" &

#env $env $solver_cmd $filename &
PID=$!
wait $PID
exit_code=$?
echo "c solver_wrapper: ==============================="
echo "c solver_wrapper: Solver finished with exit code="$exit_code
echo "f RET="$exit_code

exit $exit_code

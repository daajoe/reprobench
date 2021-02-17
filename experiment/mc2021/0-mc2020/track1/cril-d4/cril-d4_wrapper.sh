#!/usr/bin/env bash
#set -x
# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.


for i in "$@"
do
case $i in
    -e=*|--extension=*)
    EXTENSION="${i#*=}"
    shift # past argument=value
    ;;
    -s=*|--searchpath=*)
    SEARCHPATH="${i#*=}"
    shift # past argument=value
    ;;
    -l=*|--lib=*)
    LIBPATH="${i#*=}"
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
echo "FILE EXTENSION  = ${EXTENSION}"

shift $((OPTIND-1))

function interrupted(){
  kill -TERM $PID
}
trap interrupted TERM
trap interrupted INT


BIN_DIR=$(realpath $(dirname $0))
echo "$@"

output=$($BIN_DIR/d4 -mc $filename 2>/dev/null | grep "^s " | sed 's/s/s mc/g')
echo $output
exit 0

name=$(basename $1)
file=$(tempfile)
mv $file $file.$name

$BIN_DIR/BiPe -preproc $1 > $file.$name
if grep -q "^s " $file.$name ; then
    output=$(cat $file.$name | grep "^s " | sed 's/s/s mc/g')
else
    output=$($BIN_DIR/d4 -mc $file.$name 2>/dev/null | grep "^s " | sed 's/s/s mc/g')
fi
echo $output

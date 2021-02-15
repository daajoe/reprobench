#!/usr/bin/env bash
#set -x
# $1, path to the bench
BIN_DIR=$(realpath $(dirname $0))

while getopts ":m:w:p" option; do
    case "${option}" in
        m)
	    shift 
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
            ;;
        w)
	    shift 
	    name=$(basename $1)
	    file=$(tempfile)
	    mv $file $file.$name
	    
	    grep "^w " $1 | cut -d ' ' -f2- > $file.$name.w
	    grep -v "^w " $1 | sed 's/wcnf/cnf/g' > $file.$name.tmp

	    $BIN_DIR/preproc_static -vivification -eliminateLit -litImplied -iterate=10 $file.$name.tmp 2>/dev/null > $file.$name	    
	    if grep -q "^s " $file.$name ; then
		cat $file.$name | grep "^s " | sed 's/s/s wmc/g'
	    else
		$BIN_DIR/d4 -mc -wFile=$file.$name.w $file.$name 2>/dev/null | grep "^s " | sed 's/s/s wmc/g'
	    fi
            ;;
        p)
            shift 
	    name=$(basename $1)
	    file=$(tempfile)
	    mv $file $file.$name
	    
	    grep "^vp " $1 | cut -d ' ' -f2- | sed 's/ 0//g' | sed 's/  / /g' | sed 's/ /,/g' > $file.$name.v
	    
	    grep -v "^vp " $1 | sed -r 's/pcnf ([0-9]+) ([0-9]+) ([0-9]+)/cnf \1 \2/g' > $file.$name.tmp   
	    $BIN_DIR/preproc_static -vivification -eliminateLit -litImplied -iterate=10 $file.$name.tmp 2>/dev/null > $file.$name
	    if grep -q "^s " $file.$name ; then
		cat $file.$name | grep "^s " | sed 's/s/s pmc/g'
	    else
		$BIN_DIR/d4 -emc -fpv=$file.$name.v $file.$name 2>/dev/null | grep "^s " | sed 's/s/s pmc/g'
	    fi
            ;;
    esac
done

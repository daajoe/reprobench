#!/bin/bash
#set -x
BIN_DIR=$(realpath $(dirname $0))

tout_be=110
tout_be_relaxed=$(( tout_be+tout_be ))

SECONDS=0

rm -f proj*
rm -f out*
rm -f newfile*
rm -f input*

echo "c Getting indep support, timeout: ${tout_be}"
grep -v "^c" - | sed "s/pcnf/cnf/" | grep -v "^vp" > inputfile
rm -f projection
touch projection
$($BIN_DIR/bin/doalarm ${tout_be_relaxed} $BIN_DIR/bin/b_plus_e -B=projection -cpu-lim=${tout_be} inputfile) > /dev/null 2>&1
sed -i "s/V/vp/" projection
found=`grep "vp .* 0$" projection`
echo "c found is: $found"

# count support size
suppsize=100000
if [[ $found == *"vp"* ]]; then
    suppsize=`grep "vp .*0$" projection | sed "s/ /\\n/g" | wc -l`
    suppsize=$((suppsize-2))
    echo "c indep support size by B+E: $suppsize"
fi


if [[ $found == *"vp"* ]]; then
    echo "c OK, B+E succeeded"
    cp inputfile newfile2
    cat projection >> newfile2
else
    echo "c WARNING B+E did NOT succeed"
    cp inputfile newfile2
fi

sed 's/vp/c ind/g' newfile2 | sed 's/ pcnf/ cnf/g' > newfile3

tout_ganak=$(( 1780-SECONDS))
if [[ $suppsize -lt 1500 ]];then
    tout_ganak=$(( 1790-400-SECONDS ))
fi 

echo "c Trying to run Ganak, timeout: ${tout_ganak}"
$($BIN_DIR/bin/doalarm ${tout_ganak} $BIN_DIR/bin/ganak_plus_panini inputfile > output) > /dev/null 2>&1
sed -i 's/s pmc/s mc/g' output
found=`grep "s mc" output`
if [[ $found == *"s mc"* ]]; then
    cat output
    exit 0
fi
echo "c Ganak did NOT work"

tout_shortapproxmc=$(( 1790 - SECONDS ))
echo "c Running ApproxMC, timeout:${tout_shortapproxmc}"
$BIN_DIR/bin/doalarm ${tout_shortapproxmc} $BIN_DIR/bin/approxmc --verb 0 --delta 0.2 --epsilon 0.3 newfile3
exit 0

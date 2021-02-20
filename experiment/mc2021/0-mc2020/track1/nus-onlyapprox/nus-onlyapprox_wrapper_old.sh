#!/bin/bash
# set -x
BIN_DIR=$(realpath $(dirname $0))

tout_be=100
tout_ganak=500
tout_be_relaxed=$((tout_be+tout_be))
tout_approxmc=950

SECONDS=0
rm -f proj*
rm -f out*
rm -f newfile*
rm -f input*

echo "c Getting indep support, timeout: ${tout_be}"
grep -v "^c" - | sed "s/pcnf/cnf/" | grep -v "^vp" > inputfile
rm -f projection
touch projection
$($BIN_DIR/bin/doalarm ${tout_be_relaxed} $BIN_DIR/bin/arjun inputfile > projection) > /dev/null 2>&1
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

if [[ $suppsize -gt 2500 ]];then
    tout_ganak=$(( 1780-SECONDS ))
fi

if [[ $found == *"vp"* ]]; then
    echo "c OK, Arjun succeeded"
    cp inputfile newfile2
    cat projection >> newfile2
else
    echo "c WARNING B+E did NOT succeed"
    cp inputfile newfile2
fi

sed 's/vp/c ind/g' newfile2 | sed 's/ pcnf/ cnf/g' > newfile3



tout_approxmc=$((1790 - SECONDS))
echo "c Running ApproxMC, timeout: ${tout_approxmc}"
$BIN_DIR/bin/doalarm  ${tout_approxmc} $BIN_DIR/bin/approxmc --verb 0 --delta 0.15 --epsilon 0.2 newfile3 
exit 0

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Kuldeep S Meel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# If you use this code for experiments, please cite the following paper:
# "From Weighted to UnWeighted Model Counting"
# by Supratik Chakraborty, Dror Fried, Kuldeep S. Meel, Moshe Y. Vardi
# Proc. of IJCAI 2016

import sys
import os
import math
import time
import argparse
import decimal


class RetVal:
    def __init__(self, origVars, origCls, vars, totalCount, div):
        self.origVars = origVars
        self.origCls = origCls
        self.vars = vars
        self.totalCount = totalCount
        self.div = div


class Converter:
    def __init__(self, precision, verbose=False):
        self.precision = precision
        self.verbose = verbose
        self.samplSet = {}

    def pushVar(self, variable, cnfClauses):
        cnfLen = len(cnfClauses)
        for i in range(cnfLen):
            cnfClauses[i].append(variable)
        return cnfClauses

    def getCNF(self, variable, binStr, sign, origVars):
        cnfClauses = []
        binLen = len(binStr)
        cnfClauses.append([binLen+1+origVars])
        for i in range(binLen):
            newVar = binLen-i+origVars
            if sign is False:
                newVar = -1*(binLen-i+origVars)
            if binStr[binLen-i-1] == '0':
                cnfClauses.append([newVar])
            else:
                cnfClauses = self.pushVar(newVar, cnfClauses)
        self.pushVar(variable, cnfClauses)
        return cnfClauses

    def encodeCNF(self, variable, kWeight, cmpkWeight, iWeight, cmpiWeight, origvars, cls, div):
        if iWeight == 1 and kWeight == 1 and cmpiWeight == 1 and cmpkWeight == 1:
            return "", origvars, cls, div+1

        maxvars = max(iWeight,cmpiWeight)
        self.samplSet[origvars+1] = 1
        binStr = str(bin(int(kWeight)))[2:-1]
        binLen = len(binStr)
        for i in range(iWeight-binLen-1):
            binStr = '0'+binStr
        for i in range(maxvars-1):
            self.samplSet[origvars+i+2] = 1
        
        
        complementStr = str(bin(int(cmpkWeight)))[2:-1]
        cmpLen = len(complementStr)
        for i in range(cmpiWeight-cmpLen-1):
            complementStr ='0'+complementStr
        origCNFClauses = []
        if (iWeight > 0):
            origCNFClauses = self.getCNF(-variable, binStr, True, origvars)

        writeLines = ''
        for i in range(len(origCNFClauses)):
            cls += 1
            for j in range(len(origCNFClauses[i])):
                writeLines += str(origCNFClauses[i][j])+' '
            writeLines += '0\n'

        currentVar = -variable
        cnfClauses = []
        if (cmpiWeight > 0):
            cnfClauses = self.getCNF(variable, complementStr, False, origvars)
        for i in range(len(cnfClauses)):
            if cnfClauses[i] in origCNFClauses:
                continue
            cls += 1
            for j in range(len(cnfClauses[i])):
                writeLines += str(cnfClauses[i][j])+' '
            writeLines += '0\n'

        vars = origvars+max(iWeight,cmpiWeight)
        return writeLines, vars, cls, div+maxvars

    # return the number of bits needed to represent the weight (2nd value returned)
    # along with the weight:bits ratio
    def parseWeight(self, initWeight, compInitWeight):
        if type(initWeight) == float or type(initWeight) == str:
            initWeight = decimal.Decimal(initWeight)

        assert type(initWeight) == decimal.Decimal, "You must pass a float, string or a Decimal"

        assert self.precision > 1, "Precision must be at least 2"
        assert initWeight >= decimal.Decimal(0.0), "Weight must not be below 0.0"
        assert initWeight <= decimal.Decimal(1.0), "Weight must not be above 1.0"

        if self.verbose:
            print("Query for weight %s" % (initWeight))
        
        tenapprox = 10**(len(str(initWeight.normalize()))-2)

        weight = initWeight*tenapprox
        #weight = initWeight*pow(2, self.precision)
        weight = weight.quantize(decimal.Decimal("1"))
        # for CEIL, but double the error, set:
        # weight = weight.quantize(decimal.Decimal("1"), rounding=decimal.ROUND_CEILING)
        weight = int(weight)
        
        
        compweight = compInitWeight*tenapprox
        compweight = compweight.quantize(decimal.Decimal("1"))
        compweight = int(compweight)
        
        wtgcd = math.gcd(weight,compweight)
        weight = weight/wtgcd
        compweight = compweight/wtgcd
        
        divfactor = weight+compweight
        print("weight: %f compweight: %f" % (weight, compweight))
        fullprecision = int(math.ceil(math.log(max(weight,compweight),2)))
        print("tenapprox: %f fullprecision %f" % (tenapprox,fullprecision)) 

        prec = fullprecision
        if self.verbose:
            print("weight %3.5f prec %3d" % (weight, prec))

        while weight % 2 == 0 and prec > 0:
            weight = weight/2
            prec -= 1

            if self.verbose:
                print("weight %3.5f prec %3d" % (weight, prec))
        
        compprec =fullprecision
        while compweight % 2 == 0 and compprec > 0:
            compweight = compweight/2
            compprec -= 1

            if self.verbose:
                print("weight %3.5f prec %3d" % (compweight, compprec))
        
        if self.verbose:
            print("for %f and %f returning: weight %3.5f prec %3d compweight %3.5f compprec %3d" % 
                    (initWeight, compInitWeight, weight, prec, compweight, compprec))

        return weight, prec, compweight, compprec, divfactor

    #  The code is straightforward chain formula implementation
    def transform(self, lines, outputFile):
        origCNFLines = ''
        vars = 0
        cls = 0
        div = 0
        origVars = 0
        origCls = 0
        maxvar = 0
        foundCInd = False
        foundHeader = False
        for line in lines:
            if len(line) == 0:
                print("ERROR: The CNF contains an empty line.")
                print("ERROR: Empty lines are NOT part of the DIMACS specification")
                print("ERROR: Remove the empty line so we can parse the CNF")
                exit(-1)

            if line.strip()[:2] == 'p ':
                fields = line.strip().split()
                vars = int(fields[2])
                cls = int(fields[3])
                origVars = vars
                origCls = cls
                foundHeader = True
                continue

            # parse independent set
            if line[:5] == "c ind":
                foundCInd = True
                for var in line.strip().split()[2:]:
                    if var == "0":
                        break
                    self.samplSet[int(var)] = 1
                continue

            if line.strip()[0] == 'c':
                origCNFLines += str(line)
                continue

            if not foundHeader:
                print("ERROR: The 'p cnf VARS CLAUSES' header must be at the top of the CNF!")
                exit(-1)

            # an actual clause
            if line.strip()[0].isdigit() or line.strip()[0] == '-':
                for lit in line.split():
                    maxvar = max(abs(int(lit)), maxvar)
                origCNFLines += str(line)

            # NOTE: we are skipping all the other types of things in the CNF
            #       for example, the weights
            continue

        if maxvar > vars:
            print("ERROR: CNF contains var %d but header says we only have %d vars" % (maxvar, vars))
            exit(-1)

        print("Header says vars: %d  maximum var used: %d" % (vars, maxvar))

        if not foundHeader:
            print("ERROR: No header 'p cnf VARS CLAUSES' found in the CNF!")
            exit(-1)

        # if "c ind" was not found, then all variables are in the sampling set
        if not foundCInd:
            for i in range(1, vars+1):
                self.samplSet[i] = 1

        # weight parsing and CNF generation
        origWeight = {}
        transformCNFLines = ''
        normFactor = decimal.Decimal(1)
        for line in lines:
            if line.strip()[:2] == 'w ':
                fields = line.strip()[2:].split()
                var = int(fields[0])
                val = decimal.Decimal(fields[1]).normalize()
                if val == decimal.Decimal(1):
                    #print("c Skipping line due to val is 1 ", line.strip())
                    continue

                if var < 0:
                    #print("c Skipping line due to literal <0 ", line.strip())
                    continue

                # already has been declared, error
                if var in origWeight:
                    print("ERROR: Variable %d has TWO weights declared" % var)
                    print("ERROR: Please ONLY declare each variable's weight ONCE")
                    exit(-1)

                if var not in self.samplSet:
                    print("ERROR: Variable %d has a weight but is not part of the sampling set" % var)
                    print("ERROR: Either remove the 'c ind' line or add this variable to it")
                    exit(-1)

                origWeight[var] = val
                self.samplSet[var] = 1
                valprec = len(str(val))-2
                
                kWeight, iWeight, cmpkWeight, cmpiWeight, divfactor  = self.parseWeight(val, 1-val)
                normFactor *= decimal.Decimal(divfactor)
                if self.verbose:
                    representedW = decimal.Decimal(kWeight)/decimal.Decimal(2**iWeight)
                    # print("kweight: %5d iweight: %5d" % (kWeight, iWeight))
                    print("var: %5d orig-weight: %s kweight: %5d iweight: %5d represented-weight: %s"
                          % (var, val, kWeight, iWeight, representedW))
                    representedcompW = decimal.Decimal(cmpkWeight)/decimal.Decimal(2**cmpiWeight)
                    print("complevar: %5d orig-weight: %s kweight: %5d iweight: %5d represented-weight: %s"
                            % (var,1-val,cmpkWeight, cmpiWeight,representedcompW))
                # we have to encode to CNF the translation
                eLines, vars, cls, div = self.encodeCNF(var, kWeight, cmpkWeight, iWeight, cmpiWeight, vars, cls, div)
                transformCNFLines += eLines

        with open(outputFile, 'w') as f:
            f.write('p cnf '+str(vars)+' '+str(cls)+' \n')
            #f.write('c ind ')
            #for k in self.samplSet:
            #    f.write("%d " % k)
            #f.write("0\n")

            f.write(origCNFLines)
            f.write(transformCNFLines)

        return RetVal(origVars, origCls, vars, cls, normFactor)


####################################
# main function
####################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", help="Verbose debug printing", action="store_const",
        const=True)
    parser.add_argument("--prec", help="Precision (value of m)", type=int, default=10)
    parser.add_argument("inputFile", help="input File (in Weighted CNF format)")
    parser.add_argument("outputFile", help="output File (in Weighted CNF format)")
    args = parser.parse_args()

    if args.prec is None:
        print("ERROR: you must give the --prec option, e.g. --prec 7")
        exit(-1)

    decimal.getcontext().prec = 100

    startTime = time.time()
    c = Converter(precision=args.prec, verbose=args.verbose)

    # read in input CNF
    with open(args.inputFile, 'r') as f:
        lines = f.readlines()

    ret = c.transform(lines, args.outputFile)

    # ret looks like:
    #    wtVars
    #    origVars
    #    origCls
    #    vars
    #    totalCount
    #    eqWtVars

    print("Orig vars: %-7d Added vars: %-7d" % (ret.origVars, ret.vars-ret.origVars))
    print("The resulting count you have to divide by: %d" % ret.div)
    print("Time to transform: %0.3f s" % (time.time()-startTime))
    exit(0)
#########################################################
# CUED Python Statistical Spoken Dialogue System Software
#########################################################
#
# Copyright 2015-16  Cambridge University Engineering Department 
# Dialogue Systems Group
#
# Principal Authors:  Dongho Kim and David Vandyke
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################

import sys
import os
import numpy as np

#def showConfigResult(fileNamePrefix, fileNameSuffix):
def showConfigResult(dirPrefix, numStr, fileNamePrefix, fileNameSuffix, testFlag = False):


    #fileNamePrefix = sys.argv[1]
    #fileNameSuffix = sys.argv[2]

#print fileNamePrefix.split('/')[0].ljust(10)

    sampleName = dirPrefix + numStr
    #sampleName = fileNamePrefix.split('/')[0]

    print '{0:-^30}'.format(sampleName);

    (r, ra, s, sa, t, ta) = ([],[],[],[],[],[])
    rFlag, sFlag, tFlag = False, False, False

    for idx in range(1,11):
        #print idx
        #fileName = fileNamePrefix + str(idx) + fileNameSuffix
        if testFlag == False:
            fileName = dirPrefix + numStr + '/' + fileNamePrefix + str(idx) + fileNameSuffix
        else:
            fileName = dirPrefix + numStr + '_TEST/' + fileNamePrefix + str(idx) + fileNameSuffix
        print fileName
        try: 
            file = open(fileName,'r')
            for line in file:
                if 'Average reward' in line:
                    tmp = line.strip().split(' ')
                    r.append(float(tmp[-3]))
                    ra.append(float(tmp[-1]))
                    rFlag = True
                    #print r, ra

                if 'Average success' in line:
                    tmp = line.strip().split(' ')
                    s.append(float(tmp[-3]))
                    sa.append(float(tmp[-1]))
                    sFlag = True

                if 'Average turns' in line:
                    tmp = line.strip().split(' ')
                    t.append(float(tmp[-3]))
                    ta.append(float(tmp[-1]))
                    tFlag = True

            if rFlag == False and sFlag == False and tFlag == False:
                """
                r.append(float(np.nan))
                ra.append(float(np.nan))
                s.append(float(np.nan))
                sa.append(float(np.nan))
                t.append(float(np.nan))
                ta.append(float(np.nan))
                """
                r.append('--')
                ra.append('--')
                s.append('--')
                sa.append('--')
                t.append('--')
                ta.append('--')



        except IOError:
            #print 'could not open file: '  + fileName

            r.append('--')
            ra.append('--')
            s.append('--')
            sa.append('--')
            t.append('--')
            ta.append('--')
            """
            r.append(float(np.nan))
            ra.append(float(np.nan))
            s.append(float(np.nan))
            sa.append(float(np.nan))
            t.append(float(np.nan))
            ta.append(float(np.nan))
            """
            continue

    print 'ITER' + '\t' + 'num' + '\t',
    for idx in range(1,11):
        print str(idx).ljust(5) + '\t',
    print 

    print 'REWARD' + '\t' + 'avg' + '\t',
    for i in r:
        print str(i).ljust(5) +'\t',
    print

    print 'REWARD' + '\t' + 'std' + '\t',
    for i in ra:
        print str(i).ljust(5) +'\t',
    print

    print 'SUCCESS' + '\t' + 'avg' + '\t',
    for i in s:
        print str(i).ljust(5) +'\t',
    print

    print 'SUCCESS' + '\t' + 'std' + '\t',
    for i in sa:
        print str(i).ljust(5) +'\t',
    print


    print 'TURNS' + '\t' + 'avg' + '\t',
    for i in t:
        print str(i).ljust(5) +'\t',
    print

    print 'TURNS' + '\t' + 'std' + '\t',
    for i in ta:
        print str(i).ljust(5) +'\t',
    print

def main():

    usage = str(
            '\n***********************\n'
            'usage:\n'
            'arguments: python parseResults.py dirPrefix fileNamePrefix fileNameSuffix numOfGridSearch [TEST]\n\n'
            'example:\n'
            'training results: python parseResults.py gRun tra_1_ .log 1\n'
            'testing  results: python parseResults.py gRun tra_1_ .log 1 TEST\n'
            '\n***********************\n'
    )
    print usage   

    dirPrefix = sys.argv[1]
    fileNamePrefix = sys.argv[2]
    fileNameSuffix = sys.argv[3]
    if len(sys.argv) == 5:
        for i in range(0,int(sys.argv[4])):
            showConfigResult(dirPrefix, str(i), fileNamePrefix, fileNameSuffix, False)
    elif len(sys.argv) == 6 and sys.argv[5] == 'TEST':
        for i in range(0,int(sys.argv[4])):
            showConfigResult(dirPrefix, str(i), fileNamePrefix, fileNameSuffix, True)

if __name__ == "__main__":
    main()

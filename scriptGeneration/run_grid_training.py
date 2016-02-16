#!/usr/bin/env python

#########################################################
# CUED Python Statistical Spoken Dialogue System Software
#########################################################
#
# Copyright 2015-16  Cambridge University Engineering Department 
# Dialogue Systems Group
#
# Principal Authors:  Dongho Kim and David Vandyke, Pei-Hao (Eddy) Su
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


import os
import sys
import subprocess
from subprocess import Popen, PIPE, STDOUT
import socket

def Execute(command):
    print(command)
    os.system(command)

def getJobNum(output):
    jobNum=output.split(" ")[2]
    if '.' in jobNum:
        jobNum=jobNum.split('.')[0]
    return jobNum

def formCommand(queuedest, parproc, jobNum, name, configs, dialogues, step, path, erorrrate, currentPath):
    #command = "qsub -q {} -e {}.e.log -o {}.o.log -t 1-{} -hold_jid {} -S /usr/bin/env {}.py {} {} {} {}".format(queuedest, name, name, parproc, jobNum, name, dialogues, step, path, errorrate)
    command = "qsub -e {}/{}.e.log -o {}/{}.o.log -t 1-{} -hold_jid {} -S /usr/bin/env {}/{}.py {} {} {} {} {}".format(currentPath+'/'+name, name, currentPath+'/'+name, name, parproc, jobNum, currentPath+'/'+name, name, dialogues, step, path, errorrate, currentPath+'/'+name)
    for config in configs:
        command = command+" "+config

    return command

def submitJob(command):
    print "Submitting ",command
    p = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    val = p.stdout.read()
    #val=subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    print val
    jobNum=getJobNum(val)
    return jobNum
#-----------------------------------------
# Script:
#-----------------------------------------
if len(sys.argv) < 8:
    print "usage: run_grid_training.py dirname steps numdialoguesperstep parallelprocesses path errorrate stepfromwhichtocontinue config1 [config2, ..]"
    exit(1)

name = sys.argv[1]
print "name is {}".format(name)
steps = int(sys.argv[2])
print "steps are {}".format(steps)
dialogues = int(sys.argv[3])
print "dialogues are {}".format(dialogues)
parproc = int(sys.argv[4])
print "parallel processes are {}".format(parproc)
path = sys.argv[5]
print "path is {}".format(path)
errorrate = int(sys.argv[6])
print "simulation error rate is: {}".format(errorrate)
beginning = int(sys.argv[7])
print "beginning is {}".format(beginning)
assert(beginning > 0)  # steps are 1,2,3,  etc

i=8
configs=[]

hostname = socket.gethostname()

# WARNING: only entering 1 config for now. 
while i<len(sys.argv):
    configs.append(sys.argv[i])
    i+=1


currentPath = os.getcwd()
currentPath = currentPath.replace('/export/home/mlsalt-helpers/','/home/')


if beginning == 1:
    command="mkdir {}/{}".format(currentPath, name)
    Execute(command)
    for config in configs:
        command="cp {} {}/{}".format(config,currentPath, name)
        Execute(command)
    command="cp grid_training.py {}/{}.py".format(currentPath+'/'+name,name)
    #command="cp gridGPtrain.py {}/{}.py".format(name,name)
    Execute(command)
else:
    print "Starting from ",beginning

command = "cp foo.sh {}/".format(name)
Execute(command)

command="./{}".format(name)
print command
os.chdir(command)

if hostname != 'krakow':

    jobsFileName = "{}.jobs".format(name)
    jobsFile = open(jobsFileName, 'w')

    # SUBMIT THE foo.sh START DUMMY JOB.  ---------------------
    #queuedest="all.q@air063,all.q@divfproj-fs"
    queuedest =""

    #command="qsub -q {} -e {}.e.log -o {}.o.log -S /bin/bash foo.sh".format(queuedest,name,name)
    command="qsub -e {}/{}.e.log -o {}/{}.o.log -S /bin/bash {}/foo.sh".format(currentPath+'/'+name, name, currentPath+'/'+name, name, currentPath)
    jobNum=submitJob(command)
    jobsFile.write("{}\n".format(jobNum));

# SUBMIT THE ACTUAL JOBS:  ---------------------
for step in range(beginning,steps+1):
    if hostname != 'krakow':
        print "Running {} step conditioned on {}\n".format(step, jobNum)
        command=formCommand(queuedest, parproc, jobNum, name, configs, dialogues, step, path, errorrate, currentPath)
        jobNum=submitJob(command)
        print "Submitted job {}\n".format(jobNum)
        jobsFile.write("{}\n".format(jobNum));
    else:
        command = "python {}.py {} {} {} {}".format(name, dialogues, step, path, errorrate)
        for config in configs:
            command = command+" "+config
        os.system(command)

if hostname != 'krakow':
    jobsFile.close()
# END OF FILE

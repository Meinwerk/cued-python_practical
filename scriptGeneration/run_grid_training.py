#!/usr/bin/env python

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

def formCommand(queuedest, parproc, jobNum, name, configs, dialogues, step, path, erorrrate):
    command = "qsub -q {} -e {}.e.log -o {}.o.log -t 1-{} -hold_jid {} -S /usr/bin/env {}.py {} {} {} {}".format(queuedest, name, name, parproc, jobNum, name, dialogues, step, path, errorrate)
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
    print "usage: grid_training.py dirname steps numdialoguesperstep parallelprocesses path errorrate stepfromwhichtocontinur config1 [config2, ..]"
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

if beginning == 1:
    command="mkdir {}".format(name)
    Execute(command)
    for config in configs:
        command="cp {} {}".format(config,name)
        Execute(command)
    command="cp grid_training.py {}/{}.py".format(name,name)
    #command="cp gridGPtrain.py {}/{}.py".format(name,name)
    Execute(command)
else:
    print "Starting from ",beginning

command="./{}".format(name)
print command
os.chdir(command)

if hostname != 'krakow':

    jobsFileName = "{}.jobs".format(name)
    jobsFile = open(jobsFileName, 'w')

    # SUBMIT THE foo.sh START DUMMY JOB.  ---------------------
    #queuedest="all.q@air063,all.q@divfproj-fs"
    queuedest =""

    command="qsub -q {} -e {}.e.log -o {}.o.log -S /bin/bash foo.sh".format(queuedest,name,name)
    jobNum=submitJob(command)
    jobsFile.write("{}\n".format(jobNum));

# SUBMIT THE ACTUAL JOBS:  ---------------------
for step in range(beginning,steps+1):
    if hostname != 'krakow':
        print "Running {} step conditioned on {}\n".format(step, jobNum)
        command=formCommand(queuedest, parproc, jobNum, name, configs, dialogues, step, path, errorrate)
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

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


import sys
import os
from sets import Set


#-----------------------------------------
# UTILS:
#-----------------------------------------
def Execute(command):
    print command
    os.system(command)    
    
def Execute_py(command, thisTask, step, outputDirName):
    scriptName = outputDirName + '/' + str(step)+'_'+str(thisTask)+'_'+"script.sh"
    print 'scriptName', scriptName
    f = open(scriptName,"w")
    f.write("#!/bin/bash\n")
    f.write("python "+command)
    f.close()
    os.system("bash "+scriptName)   

def getCommand(config,error,seed,thisTask,step,numDialogs,path,outputDirName):
    # removed the -l policy settings - do this in config now.
    return "{}/simulate.py -C {} -r {} -s {} -n {} --nocolor > {}/tra_{}_{}.log".format(path,config,str(error),\
                    str(seed),str(numDialogs),outputDirName,str(thisTask),str(step))
    
def seed(step, totalDialogues, totalTasks, thisTask):
    return (step-1)*totalDialogues*totalTasks + (thisTask-1)*totalDialogues + 1
    
def getName(name,task, step):
    return name+"_"+str(task)+"."+str(step)
    
def getDictParam(name,task, step):
    fullname = getName(name, task, step)
    dictionary = fullname+".dct"
    parameters = fullname+".prm"
    return [dictionary, parameters]

def extractGlobalandLocalPolicies(line): 
    elems = line.strip().split('=')[1].lstrip().split(';');
    return elems 
    
def getGlobalandLocalPolicies(configs, term="inpolicyfile"):
    policyset=Set([])  # just use list?
    for config in configs:
        configfile=open(config, 'r')
        for line in configfile:
            if term in line:
                elems=extractGlobalandLocalPolicies(line)
                for elem in elems:
                    policyset.add(elem)
        configfile.close()
    names = list(policyset)
    if len(names) ==1:
        if names[0] == '':
            names = []
    return names

#-----------------------------------------
# SCRIPT:
#-----------------------------------------
if len(sys.argv)<6:
    print "usage: grid_training.py totaldialogues step pathtoexecutable errorrate outputDirName config1 [config2 config3...]"
    exit(1)

#print sys.argv
totalDialogues = int(sys.argv[1])
step = int(sys.argv[2])
path = sys.argv[3]
error = int(sys.argv[4])  # int() doesn't actually matter here
outputDirName = sys.argv[5]
configs = []

i=6
# as in run_grid_pyGPtraining.py -- only entering a single config
while i<len(sys.argv):
    configs.append(sys.argv[i])
    i=i+1

thisTask = 1
totalTasks = 10
if 'SGE_TASK_ID' in os.environ:
    thisTask = int(os.environ['SGE_TASK_ID'])
    totalTasks = int(os.environ['SGE_TASK_LAST'])

# Write the config file for this task and step number, working from raw config input
suffConfigs=[]
innames = getGlobalandLocalPolicies(configs, term="inpolicyfile")
outnames = getGlobalandLocalPolicies(configs, term="outpolicyfile")
if len(outnames) == 0:
    outnames = ['z']
if len(innames) == 0 and step > 1 :
    innames = outnames
elif len(innames) == 0 and step == 1:
    innames = ['junk']

for i in range(len(configs)):
    configName = configs[i].split('/')[-1]
    suffConfig = outputDirName+'/'+str(thisTask)+"_"+str(step)+"_"+configName   #+configs[i]
    suffConfigs.append(suffConfig)
    outfile=open(suffConfig, 'w');
    openConfig = open(configs[i],'r')
    foundIN, foundOUT = False, False
    for line in openConfig:
        # Note: need to be careful of comments in config file. will still be read here ...
        if 'inpolicyfile' in line:
            if '#' in line:
                print "Warning - be carefull about comments in config - this isnt #inpolicyfile is it?"
            #elems=extractGlobalandLocalPolicies(line)
            elems = innames
            policies=[]
            for elem in elems:  
                policies.append(getName(elem,thisTask, step-1))  # such that out has same task and step as config file
            if len(policies) > 1:
                policy=';'.join(policies)
            else:
                policy=''.join(policies)
            outfile.write('inpolicyfile = '+policy+"\n")
            foundIN = True
            continue
        if 'outpolicyfile' in line:
            if '#' in line:
                print "Warning - be carefull about comments in config - this isnt #outpolicyfile is it?"
            #elems=extractGlobalandLocalPolicies(line)
            elems = outnames
            policies=[]
            for elem in elems:  
                policies.append(getName(elem,thisTask, step))
            if len(policies) > 1:
                policy=';'.join(policies)
            else:
                policy=''.join(policies)
            outfile.write('outpolicyfile = '+policy+"\n")
            foundOUT = True
            continue
        else:
            EpsDenominator = 1000.0
            start = 1 - (1-0.1)*float(step-1)*totalDialogues/EpsDenominator
            if 'epsilon_start = 1' in line:
                outfile.write('epsilon_start = '+ str(start) + '\n')
            else:
                outfile.write(line)

    if not foundIN: 
        exit("you must specify inpolicyfile - can add section in this script here to write it to config")
    if not foundOUT:
         exit("you must specify outpolicyfile - can add section in this script here to write it to config") 
    outfile.close()
    openConfig.close()
  
seed=seed(step, totalDialogues, totalTasks, thisTask);


if len(suffConfigs)>1:
    for config in suffConfigs:
        command=getCommand(config,error,seed,thisTask,step,totalDialogues,path,outputDirName)
        Execute(command)
        seed+=totalDialogues
else:
    # if there is only one domain
    command=getCommand(suffConfigs[0],error,seed,thisTask,step,totalDialogues,path,outputDirName)
    Execute_py(command, thisTask, step, outputDirName)


#END OF FILE

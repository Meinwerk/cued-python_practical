import json
import copy
import re
import sys

'''
each line in .txt rules starts with:
# - dont care
\n - dont care
task
entity, type - the things in here make up 'requestable' 
method, discourseAct
*OTHER*  - these are slots - 
'''

remove_from_req = ['entity','location','type','venue','restaurant','device','laptop','hotel']

def txt2json(txtfile):
    # create base dictionary:
    SET_SLOTS = False
    ont = dict.fromkeys(['type','requestable','discourseAct','system_requestable','method','informable'])
    ont['discourseAct'] = [
        "ack", 
        "hello", 
        "none", 
        "repeat", 
        "silence", 
        "thankyou"
    ] 
    ont['method'] = [
        "none", 
        "byconstraints", 
        "byname", 
        "finished", 
        "byalternatives", 
        "restart"
    ]
   
    # step through txt rules
    with open(txtfile+'.txt','r') as txtFILE:
        f = txtFILE.readlines()

        for i in range(len(f)):
            line = f[i]
            if line[0] == '#':
                continue
            if 'task' in line:
                continue
            if 'entity' in line:
                # assume entity comes before type:
                req = re.findall(r"[\w']+", line)
                continue
            if 'type' in line:
                req += re.findall(r"[\w']+", line) 
                for x in remove_from_req:
                    while x in req:
                        req.remove(x)  # this should remove all occurences.
                print 'requestable slots are (ie all slots)'
                req_final = copy.deepcopy(req)
                ont['requestable'] = req_final
                print ont['requestable']
                ont['informable'] = dict.fromkeys(req)
                # also set the breakup of informable and requestable slots via inform_req_lines - 
                # do this MANUALLY - easier! but gives some confidence/checks:
                sys = []
                for slot in req:
                    ans = raw_input('is slot: '+slot+' SYSTEM REQUESTABLE?')
                    if ans == 'y':
                        sys.append(slot)
                print 'system requestable slots are:'
                print sys
                ont['system_requestable'] = sys
                SET_SLOTS = True
                continue
            if 'method' in line:
                continue
            if 'discourseAct' in line:
                continue
            if SET_SLOTS:
                #for slot in ont['requestable']:
                for slot in req:
                    #print slot
                    #print line
                    #raw_input()
                    if slot in line and ('"' not in line):
                        count = 0
                        while ');' not in f[i+count]:
                            count += 1
                        values = f[i+1:i+count]
                        #raw_input('-- print values now:')
                        #print values
                        #raw_input('check')
                        vals = []
                        for v in values:
                            x = v.split('"')
                            vals.append(x[1])
                        print vals
                        print '^^ are for slot: ', slot
                        raw_input('check values parsed')
                        ont['informable'][slot] = vals
                        req.remove(slot)
                        break
    writeto = open(txtfile+'.json','w')
    json.dump(ont,writeto)
    writeto.close()


if __name__ == '__main__':
    infile = sys.argv[1]
    raw_input('THIS FILE IS WRITTEN JUST TO PARSE THE rules remaining in .txt format only - wont work for TT')
    raw_input('----You are about to create a .json of: '+infile)
    txt2json(infile)



"""
Attractions - seetype, unitype, entstype, sportsvenue  # see how many entities here - possibly split this up?
Ammenities - amtype, shoptype 
Hotels - staytype,  
Transport - transtype 

"""
#UTILS:
#------------------------------------------
def determine_type(entlist):
    #types = []
    for line in entlist:
        if "type(" in line and line[0:5] != "type":   #find the first Xtype() -- resolve conflicts based on first.
            #types.append(line)
            entype = line.split('"')[0][0:-1]  #0 not 1 here - want the Xtype() not the value 
            return entype

def fix_id(entlist, newid):
    for line in entlist:
        if "id(" in line:
            break
    entlist.remove(line)
    entlist = ['id("'+str(newid)+'")\n'] +entlist 
    return entlist

def findOccurences(s, ch):
    return [i for i, letter in enumerate(s) if letter == ch]

def remove_odd_chars(entlist):
    newent = []
    for line in entlist:
        if len(line) !='\n':
            inds = findOccurences(line, '"')
            print line
            print inds
            if len(inds) != 2:
                break  #exit("error")
            newent.append(line[0:inds[1]+2]+'\n')
    return newent


#CODE:
#------------------------------------------
writeFileNames = {"CamAttrac-dbase.txt":["seetype", "unitype", "entstype", "sportsvenue"],
            "CamAmen-dbase.txt":["amtype", "shoptype"],
            "CamHotels-dbase.txt":["staytype"],
            "CamTrans-dbase.txt":["transtype"]
        }
writeFiles = dict.fromkeys(writeFileNames.keys())
for k in writeFiles.keys():
    writeFiles[k] = open(k,"w")
count = dict.fromkeys(writeFiles.keys(),0)

originalDBASEfile = "CIdbase_V14.txt"
odbase = open(originalDBASEfile, "r")
other = open("other_ents.txt","w")

ent = []
written = False
for line in odbase:
    if line == '\n':
        continue
    if 'id("' in line:
        if len(ent):
            enttype = determine_type(ent)
            #print ent
            #print enttype
            #raw_input("check type")
            for k,v in writeFileNames.iteritems():
                if enttype in v: 
                    ent = fix_id(ent,count[k])
                    #print ent
                    #raw_input("check ent after id fix")
                    ent = remove_odd_chars(ent)
                    count[k] += 1
                    for entline in ent:
                        writeFiles[k].write(entline)
                    writeFiles[k].write('\n')
                    written = True
            if written is False:
                for entline in ent:
                    other.write(entline)
                other.write('\n')
                
        ent = []
        written = False
        ent.append(line)
    else:
        ent.append(line)

#CLOSE OPEN FILES
odbase.close()
other.close()
for k in writeFiles.keys():
    writeFiles[k].close()

#END OF FILE

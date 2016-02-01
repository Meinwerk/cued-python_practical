raw_input("Toshiba website doesn't work -- manually going to create this as there are only ~10 products")

slots = ["id","name","weight","weightrange","price","hdmi","internet","pricerange","kind","type"]
#ent = dict.fromkeys(slots)
db = open("TSBplayer-dbase.txt","w")
for idcount in range(10):
    for slot in slots:
        if slot == "id":
            line = slot + '("'+str(idcount)+'")\n'
        else:
            line = slot + '("")\n'
        db.write(line)
    db.write("\n")
db.close()



exit("DONE WITH MANUAL PART")
#-----------------------------------------------------
import urllib
import json
import my_html_utils as utils



types = {'canvio-slim-for-mac':'http://www.toshiba.eu/hard-drives/portable/canvio-slim-for-mac/',
        'canvio-slim':'http://www.toshiba.eu/hard-drives/portable/canvio-slim/',
        'canvio-connect-II':'http://www.toshiba.eu/hard-drives/portable/canvio-connect-II/',
        'store-alu-tv-kit':'http://www.toshiba.eu/hard-drives/portable/store-alu-tv-kit/',
        'canvio-alu':'http://www.toshiba.eu/hard-drives/portable/canvio-alu/',
        'canvio-ready':'http://www.toshiba.eu/hard-drives/portable/canvio-ready/',
        'canvio-plus':'http://www.toshiba.eu/hard-drives/portable/canvio-plus/',
        'canvio-basics':'http://www.toshiba.eu/hard-drives/portable/canvio-basics/',
        }

blutypes = {
        'canvio-desk':'http://www.toshiba.eu/hard-drives/desktop/canvio-desk/',
        }
"""
USER INFORMABLE:
-pricerange
-kind    # portable or desktop
-name
-series
-weightrange
-interface
-maxtransrate
-capacity

USER REQUESTABLE:
-weight
-price
-decription (called others on website)
-requirements
-extras (called box content on website)
-enclosure
-color
-filesystem
-power
-dimensions

"""

slots = ["name", "series","pricerange", "price","weight","weightrange","interface","maxtransrate","kind",
        "capacity","description","requirements","extras","enclosure","color", "filesystem","power","dimensions"]

entity_template = dict.fromkeys(slots)
entity_template["id"] = None
entity_template["type"] = "externalhd"
write_list_order = ["id"] +["type"] + slots


exthdont = {"type":"externalhd",
    "requestable": [
            "weight",
            "price",
            "decription",
            "requirements",
            "extras",
            "kind",
            "enclosure",
            "color",
            "filesystem",
            "power",
            "dimensions",
            "pricerange",
            "name",
            "series",
            "weightrange",
            "interface",
            "maxtransrate",
            "capacity"
    ],  
    "discourseAct": [
        "ack", 
        "hello", 
        "none", 
        "repeat", 
        "silence", 
        "thankyou"
    ], 
    "method": [
        "none", 
        "byconstraints", 
        "byname", 
        "finished", 
        "byalternatives", 
        "restart"
    ],
    "system_requestable": [
            "pricerange",
            "name",
            "kind",
            "series",
            "weightrange",
            "interface",
            "maxtransrate",
            "capacity"
    ],
    "informable": ''
            }

exthdont["informable"] = dict.fromkeys(exthdont["system_requestable"])
exthdont["informable"]["name"] = None
print exthdont["informable"]
dbfilename = "TSBextHDdbase.txt"
ontfilename = "TSBextHDrules.json"


###### FOR PARSING HTML PAGE:
start_info_section_identifier = '<table class="productSpecTable">'  # this part of HTML source 
end_info_section_identifier = '</table>'

ids = {"interface":["Interface</td>"],
        "maxtransrate": ["Max. transfer rate</td>"],
        "weight": ["Weight with Ped.Stand (kg) :"],
        "enclosure": ["Enclosure</td>"],
        "color": ["Color</td>"],
        "capacity": ["Capacity</td>"],
        "filesystem": ["File system</td>"],
        "power": ["Power</td>"],
        "dimensions": ["Dimensions</td>"],
        "weight": ["Weight</td>"],
        "description": ["Others</td>"],
        "requirements": ["System requirements</td>"],
        "extras": ["Box content</td>"],
        }

# needed?
#accessories_replacement = {}
#accessories_replacement["Remote Control (Type) :"] = "Remote control"
#accessories_replacement["3D Glasses (Passive)"] = "Passive 3D glasses"
#accessories_replacement["3D Glasses (Active Shutter) :"] = "Active 3D glasses"
#accessories_replacement["European Warranty"] = "European Warranty"


#----------------------------------------------------

# To determine the binnings of ranges we need to know the range on first run thru:
weightranges = []
priceranges = []

# some pages are missing some info - im making it up - record for which here:
fiction = {}
# SET some default values for our lies!
#TODO
defaultvalues = dict.fromkeys(entity_template)
defaultvalues["price"] = '0'
defaultvalues["pricerange"] = 'cheap'
defaultvalues["others"] = 'none'
defaultvalues["weight"] = '200g'
defaultvalues["power"] = 'not available'


# all values in all slots - to sort out ontology later:
allvals = dict.fromkeys(exthdont["system_requestable"])
allvals["name"] = []
for k in allvals.keys():
    allvals[k] = []   # this is rubbish, but dict.fromkeys() was doing something odd...
#print allvals
#raw_input("chcekc allvals init")

parsedHTMLpages = []
JUST_PRINT_NONE = True
idcounter=1
dbfile = open(dbfilename,"w")
kind = [types, desktoptypes]
kindNum = 0
for kindNum in [0,1]:
    for key, page in kind[kindNum].iteritems():
        print "OPENING MAIN PAGE: "+page
        thispage = urllib.urlopen(page)
        htmlSource = thispage.readlines()
        thispage.close()
        #print htmlSource
        #raw_input('source page')

        for line in htmlSource:
            logic1 = page in line
            logic2 = 'where-to-buy/' not in line
            logic3 = 'style="text-decoration:' not in line
            logic4 = 'title="View Details"' not in line
            logic5 = 'rel="alternative"' not in line
            if logic1 and logic2 and logic3 and logic4 and logic5: # look for links to the child products
                # load entity HTML source
                entity_page = utils.get_href(line) 
                print 'NEW ENTITY PAGE: '+entity_page
                parsedHTMLpages.append(entity_page)
                temp = urllib.urlopen(entity_page)
                entitySource = temp.readlines()
                temp.close()
                print "READ"

                # parse entity HTML source into a db object
                entity = dict.fromkeys(entity_template)
                entity["id"] = str(idcounter); idcounter+=1
                entity["series"] = key
                if kindNum == 0:
                    entity["kind"] = "portable"
                elif kindNum == 1:  # should be
                    entity["kind"] = "desktop"
                entity["name"] = utils.get_name(entity_page) 
                entity["price"] = '0'   # there is no price information avialable
                inInfo = False
                print ":: Starting to parse entitySource"
                for i in range(len(entitySource)):
                    entline = entitySource[i]
                    #raw_input('now parsing entity source html')
                    if start_info_section_identifier in entline:
                        print ":: Found information HTML block"
                        inInfo = True
                    if inInfo:
                        # look for ids in entline:                    
                        for idkey,idval in ids.iteritems():   # gather out the information as required 
                            if idval[0] in entitySource[i]:
                                entity[idkey] = utils.get_info(entitySource[i+2])
                                i = i+2
                                #print entity[idkey]
                                #raw_input("info above")


                    if end_info_section_identifier in entline and inInfo is True:
                        inInfo = False 
                        print ":: End of information HTML block"
                        fiction[entity["id"]] = []
                        if None in entity.values():
                            none_keys = []
                            for k,v in entity.iteritems():                             
                                if v is None and k is not "type":
                                    none_keys.append(k)
                                    if k not in ["pricerange", "price"]:
                                        fiction[entity["id"]].append(k)
                                    if k == "description":
                                        entity[k] = utils.get_description(entitySource)
                                        print entity[k]
                                        #raw_input("check the alternative description")
                                    else:
                                        entity[k] = defaultvalues[k]
                                if JUST_PRINT_NONE and v is not None:
                                    continue
                                print k, ' -- ', v
                            if len(none_keys):
                                print none_keys
                                print "WE MISSED THE ABOVE INFO"
                                #raw_input("ERROR - we missed someinfo with this entity")
                        else:
                            break
                        # On first run thru - add the screen size info:
                        weightranges.append(entity["weight"])
                        # Usinge above after running once already, determined the following for screensize binning:
                        entity["weightrange"] = utils.bin_weight(entity["weight"])
                        print entity["weight"]
                        print entity["weightrange"]
                        #raw_input("check weight range")

                # write the entity to database:
                #print entity
                #raw_input("entity is: ^")
                for slot in write_list_order:
                    writeline = utils.form_write_string(slot,entity[slot])
                    if slot in allvals.keys():
                        if entity[slot] not in allvals[slot]:
                            #print allvals[slot]
                            #print entity[slot]
                            #raw_input(" is and add")
                            allvals[slot] += [entity[slot]]  # something odd happeninghere - append() was odd
                            #print allvals
                            #raw_input("check all vals")
                    dbfile.write(writeline)
                    print writeline
                    #raw_input("inspect writeline")
                dbfile.write('\n') # put a newline btw each entity


        print("-------------------end type: "+page)

print "Number of entities is: "+str(len(parsedHTMLpages))
print idcounter
print sorted(weightranges)
    


# Record which things we made up
with open("fiction_TSB_extHD.json","w") as f:
    json.dump(fiction, f)

dbfile.close()


# write the ontology now that we've seen everything:
exthdont["informable"]["name"] = allvals["name"]
for slot in exthdont["informable"]:
    exthdont["informable"][slot] = allvals[slot]

with open(ontfilename, "w") as f:
    json.dump(exthdont,f)
#raw_input()



################################################################


#END OF FILE

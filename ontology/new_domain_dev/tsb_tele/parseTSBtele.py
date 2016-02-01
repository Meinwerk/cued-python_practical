warning = " Note that type() is not printed against each entity, and the ontology requestable slots are missing the sys_requestable ones. I manually/externally to this file fixed this"
raw_input(warning)


import urllib
import json
import my_html_utils as utils
#tele_link = "http://www.toshiba.eu/television/consumer-tvs/led/"
#page = urllib.urlopen(tele_link)
#htmlSource = page.readlines()
#page.close()
#print htmlSource
#print type(htmlSource)
#raw_input()
#for line in htmlSource:
#    print line
#    raw_input()






types = {'T5':'http://www.toshiba.eu/television/consumer-tvs/led/t5/',
        'L7':'http://www.toshiba.eu/television/consumer-tvs/led/l7/',
        'L6':'http://www.toshiba.eu/television/consumer-tvs/led/l6/',
        'E2':'http://www.toshiba.eu/television/consumer-tvs/led/e2/',
        'L9':'http://www.toshiba.eu/television/consumer-tvs/led/l9/',
        'L5':'http://www.toshiba.eu/television/consumer-tvs/led/l5/',
        'L2':'http://www.toshiba.eu/television/consumer-tvs/led/L2/',   # an error on Toshiba page!
        'W3':'http://www.toshiba.eu/television/consumer-tvs/led/w3/',
        'W2':'http://www.toshiba.eu/television/consumer-tvs/led/w2/',
        'D3':'http://www.toshiba.eu/television/consumer-tvs/led/d3/',   # THERE are no D3 products!
        'L1':'http://www.toshiba.eu/television/consumer-tvs/led/l1/',
        'W1':'http://www.toshiba.eu/television/consumer-tvs/led/w1/',
        'D1':'http://www.toshiba.eu/television/consumer-tvs/led/d1/',
        }
"""
USER INFORMABLE:
-pricerange
-eco
-screensizerange
# REMOVED -- -weightrange
-hdmi
-usb  (binary)
-name
-series

USER REQUESTABLE:
# REMOVED -- -weight  (with stand/pedastal)
-screensize (inches)
-price
-audio
-accessories
-power (home mode)
-cabinet
-pixels
"""
slots = ["name", "series","pricerange", "price","eco","screensizerange","hdmi","usb",
        "screensize","audio","accessories","power","cabinet","pixels"]
# REMOVING THE WEIGHT SLOT - info never available
#slots.remove("weightrange")
#slots.remove("weight")
entity_template = dict.fromkeys(slots)
entity_template["id"] = None
write_list_order = ["id"] + slots


teleont = {"type":"television",
    "requestable": [
    "screensize",
    "price",
    "audio",
    "accessories",
    "power",
    "cabinet",
    "pixels"
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
        "eco",
        "screensizerange",
        "hdmi",
        "usb",
        "series"
    ],
    "informable": ''
            }

teleont["informable"] = dict.fromkeys(teleont["system_requestable"])
teleont["informable"]["name"] = None
print teleont["informable"]
dbfilename = "TSBteledbase.txt"
ontfilename = "TSBtelerules.json"


###### FOR PARSING HTML PAGE:
start_info_section_identifier = '<table class="productSpecTable">'  # this part of HTML source 
#end_info_section_identifier = '<section class="pageDisclaimer">'  
end_info_section_identifier = '</table><!-- end product spec table -->'
ids = {"screensize":["Diagonal Screen Size (inch) :"],
        "eco": ["Energy Label :"],
        "weight": ["Weight with Ped.Stand (kg) :"],
        "audio": ["NICAM", "CEVO", "Audyssey"],  
        "accessories": ["Remote Control (Type) :",
                        "3D Glasses (Passive)",
                        "3D Glasses (Active Shutter) :",
                        "European Warranty"],
        "usb": ["Video (USB) :"],
        "hdmi": ["Number of HDMI"],   # will be two of these, just sum them.  side and back
        "power": ["Power Consumption EN62087 - Home Mode (W) :"],   #may not be everywhere
        "cabinet": ["Colour :"],
        "pixels": ["Panel Resolution :"],
        #"name": ["<h2>Part number:&nbsp;"]
        }
#European Warranty
accessories_replacement = {}
accessories_replacement["Remote Control (Type) :"] = "Remote control"
accessories_replacement["3D Glasses (Passive)"] = "Passive 3D glasses"
accessories_replacement["3D Glasses (Active Shutter) :"] = "Active 3D glasses"
accessories_replacement["European Warranty"] = "European Warranty"


#----------------------------------------------------

# To determine the binnings of ranges we need to know the range on first run thru:
screensizeranges = []
priceranges = []

# some pages are missing some info - im making it up - record for which here:
fiction = {}
# SET some default values for our lies!
defaultvalues = dict.fromkeys(entity_template)
defaultvalues["usb"] = '0'
defaultvalues["power"] = '40'
defaultvalues["eco"] = "B"
defaultvalues["price"] = '0'
defaultvalues["pricerange"] = 'cheap'
defaultvalues["screensizerange"] = 'small'


# all values in all slots - to sort out ontology later:
allvals = dict.fromkeys(teleont["system_requestable"])
allvals["name"] = []
for k in allvals.keys():
    allvals[k] = []   # this is rubbish, but dict.fromkeys() was doing something odd...
#print allvals
#raw_input("chcekc allvals init")

# check
#for slot in teleont["informable"]:
#    print slot
#raw_input("del")

parsedHTMLpages = []
JUST_PRINT_NONE = True
idcounter=1
dbfile = open(dbfilename,"w")
for key, page in types.iteritems():
    thispage = urllib.urlopen(page)
    htmlSource = thispage.readlines()
    thispage.close()

    for line in htmlSource:
        logic1 = page in line
        logic2 = 'rel="alternative"' not in line
        logic3 = 'style="text-decoration:' not in line
        logic4 = 'title="View Details"' not in line
        if logic1 and logic2 and logic3 and logic4: # look for links to the child products
            # load entity HTML source
            entity_page = utils.get_href(line) 
            print 'NEW ENTITY PAGE: '+entity_page
            parsedHTMLpages.append(entity_page)
            temp = urllib.urlopen(entity_page)
            entitySource = temp.readlines()
            temp.close()
            # parse entity HTML source into a db object
            entity = dict.fromkeys(entity_template)
            entity["hdmi"] = 0  # will be adding to this
            entity["accessories"] = "" # will add to this
            audioorder = dict.fromkeys(ids["audio"], False)
            entity["id"] = str(idcounter); idcounter+=1
            entity["series"] = key
            entity["name"] = utils.get_name(entity_page) 
            entity["price"] = '0'   # there is no price information avialable
            inInfo = False
            print ":: Starting to parse entitySource"
            for entline in entitySource:
                if start_info_section_identifier in entline:
                    print ":: Found information HTML block"
                    inInfo = True
                if inInfo:
                    # look for ids in entline:                    
                    for idkey,idval in ids.iteritems():   # gather out the information as required 
                        # deal with audio, etc slots that are a bit difficult
                        if idkey == "audio":
                            for val in idval:
                                if val in entline:
                                    audioorder[val] = True
                        if idkey == "hdmi":
                            if idval[0] in entline:
                                entity["hdmi"] += utils.get_info_hdmi(entline)
                        if idkey == "accessories":
                            for val in idval:
                                if val in entline:
                                    entity["accessories"] += accessories_replacement[val] + ', ' 
                        else:
                            if idval[0] in entline:   # easier slots, with only 1 thing to look for 
                                if idkey == "usb":
                                    entity[idkey] = utils.get_usb_info(entline)
                                if idkey == "cabinet":
                                    entity[idkey] = utils.get_info_cabinet(entline)
                                elif idkey in ['screensize','eco','power', 'weight']:
                                    entity[idkey] = utils.get_info(entline)
                                elif idkey == 'pixels':
                                    entity[idkey] = utils.get_info_pixels(entline)
                if end_info_section_identifier in entline:
                    # FINALISE Audio
                    if audioorder["Audyssey"]:
                        entity["audio"] = "Audyssey"
                    elif audioorder["CEVO"]:
                        entity["audio"] = "CEVO"
                    else:
                        entity["audio"] = "NICAM"    
                    # On first run thru - add the screen size info:
                    screensizeranges.append(float(entity["screensize"]))
                    # Usinge above after running once already, determined the following for screensize binning:
                    entity["screensizerange"] = utils.bin_screensize(entity["screensize"])
                    print ":: End of information HTML block"
                    fiction[entity["id"]] = []
                    if None in entity.values():
                        none_keys = []
                        for k,v in entity.iteritems():                             
                            if v is None:
                                none_keys.append(k)
                                if k not in ["pricerange", "price"]:
                                    fiction[entity["id"]].append(k)
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
            # write the entity to database:
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
print sorted(screensizeranges)
    


# Record which things we made up
with open("fiction_TSB_tele.json","w") as f:
    json.dump(fiction, f)

dbfile.close()


# write the ontology now that we've seen everything:
teleont["informable"]["name"] = allvals["name"]
for slot in teleont["informable"]:
    teleont["informable"][slot] = allvals[slot]

with open(ontfilename, "w") as f:
    json.dump(teleont,f)
#raw_input()



################################################################
"""JUNK"""
def _form_present(line,instring):
    form = '<a id="'+instring+'" name="'+instring+'"'
    if form in line:
        return



#END OF FILE

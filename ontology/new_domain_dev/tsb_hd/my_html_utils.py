doprint = False

def get_href(line):
    part=line.split('>')[0]
    if doprint:
        print line
        print part
        raw_input()
    return part.split('"')[1]

def get_name(line):
    temp = line.split('/')
    if False: #doprint:
        print "in get_name"
        print temp[-2]
        raw_input()
    return temp[-2]

def get_description(htmlsource):
    # used if no description:
    find = '<meta name="description"'
    for line in htmlsource:
        if find in line:
            temp = line.split('"')
    d = temp[3]
    #if len(d) > 50:
    #    print d
    #    d = raw_input("TOO LONG - enter your own summary of that!\n")
    if len(d) > 50:
        d = d.split('.')[0]
    return d.lower()


def get_info(line):
    temp =line[0:-8]  # remove  <br />
    if '\t' in temp:
        temp = temp.strip('\t')
    if '<br>' in temp:
        temp = temp.replace('<br>','')
    if doprint:
        print line
        print temp
        raw_input()
    return temp

def form_write_string(slot,value):
    if doprint:
        print slot
        print value
    return slot + '("'+str(value)+'")'+'\n'

def bin_weight(str_weight):
    if 'max.' in str_weight:
        str_weight = str_weight.replace("max.","")
    if 'g' in str_weight:
        str_weight = str_weight.replace("g",'')
    if '.' in str_weight:
        str_weight = str_weight.replace('.','')

    str_weight = str_weight.replace(" ","")
    print str_weight
    
    s = float(str_weight)
    if s<160:
        return "light"
    if s>200:
        return "heavy"
    return "midweight"

#END OF FILE

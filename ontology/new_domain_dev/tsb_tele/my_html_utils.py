doprint = False

def get_href(line):
    part=line.split('>')[0]
    return part.split('"')[1]

def get_name(line):
    temp = line.split('/')
    return temp[-2]

def get_usb_info(line):
    if ':' in line:
        return '1'  # not True, use same format as TSB laptops
    else:
        return '0'


def get_info(line):
    temp = line.split(':')
    temp = temp[1].split(' ')
    if doprint:
        print line.strip('\n')
        print temp[1]
    return temp[1]

def get_info_hdmi(line):
    temp = line.split(':')
    temp = temp[1].split(' ')
    if doprint:
        print line.strip('\n')
        print int(float(temp[1]))
    return int(float(temp[1]))


def get_info_cabinet(line):
    temp = line.split(':')
    temp1 = temp[1].split('<')
    if doprint:
        print line.strip('\n')
        print temp1[0]
    return temp1[0]
    

def get_info_pixels(line):
    temp = line.split(':')
    temp = temp[1].split(' ')
    bits = temp[1:4]
    final = ''.join(bits)
    if doprint:
        print line.strip('\n')
        print final
    return final


def form_write_string(slot,value):
    if doprint:
        print slot
        print value
    return slot + '("'+str(value)+'")'+'\n'

def bin_screensize(str_size):
    s = float(str_size)
    if s<32.0:
        return "small"
    if s>40.0:
        return "large"
    return "medium"

#END OF FILE

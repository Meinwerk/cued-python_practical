from lxml import html
import requests

link = "/hotel/gb/nobleo-accordia.html?aid=303948;label=cambridge-Pu7oq8AHHXmcJjv7tixD%2AQS8394963021%3Apl%3Ata%3Ap1110%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-139465405%3Alp1006598%3Ali%3Adec%3Adm;sid=7bb6f329bdae8515f6e043641341d2e6;dcid=4"
"""
page = requests.get('http://www.booking.com'+link)
print page
print type(page)
raw_input()
tree = html.fromstring(page.text)

print tree
for t in tree:
    print t
    raw_input('lines?')
"""

"""
Source page:
    http://www.booking.com/destination/city/gb/cambridge.en-us.html?aid=303948;label=cambridge-Pu7oq8AHHXmcJjv7tixD%2AQS8394963021%3Apl%3Ata%3Ap1110%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-139465405%3Alp1006598%3Ali%3Adec%3Adm;sid=7bb6f329bdae8515f6e043641341d2e6;dcid=4;inac=0&

and for Attractions:
    http://www.visitcambridge.org/things-to-do/museums-galleries-and-attractions/museums
"""

import urllib
page = urllib.urlopen('http://www.booking.com'+link)
htmlSource = page.read()
page.close()
print htmlSource
print type(htmlSource)


"""
-address
-numStars
-internet
-parking
-children
-pets
-cards accepted
-languages spoken
-phone number
-area
"""

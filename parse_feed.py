#!/usr/bin/python3

# script to fetch the XML (ugh) feed that powers http://ra-state.phys.utas.edu.au/, convert to JSON and publish to local broker
# we may as well wrangle into a known json format, ie https://www.atnf.csiro.au/vlbi/dokuwiki/doku.php/lbaops/jsonmonitoring

# Scope creep will be to add the configuration so that home assistant automatically imports the sensors

import requests
from xml.etree import ElementTree
from collections import defaultdict
import json


url = 'http://ra-state.phys.utas.edu.au/cgi-bin/mt_pleasant_26_xml.pl'
#url = 'http://ra-state.phys.utas.edu.au/cgi-bin/ceduna_30_xml.pl'

response = requests.get(url)

stash = defaultdict(dict)
root = ElementTree.fromstring(response.content)
for child in root:
    if child.tag == 'id':  # don't make this a sub-dict
        stash[child.tag] = child.text.strip()
    elif 'id' in child.attrib:
        stash[child.tag][child.attrib['id']] = child.text.strip()
        if 'class' in child.attrib:
            stash['warnings'][child.attrib['id']] = child.text.strip()
    else:
         stash[child.tag] = child.text.strip()

#print(json.dumps(stash))

# Now we have stash as a usable python dict, build up a new dict in the ATNF standard names
atnf = {}
atnf['antennaName'] = str(stash['telescope'])
atnf['infoTime'] = str(stash['time']['ut_date'] + ' ' + stash['time']['utc'])
atnf['rightAscensionICRF'] = str(stash['coord']['ra2000'])
atnf['declinationICRF'] = str(stash['coord']['dec2000'])
atnf['azimuth'] = float(stash['coord']['az'])
atnf['elevation'] = float(stash['coord']['el'])
atnf['state'] = str(stash['antenna']['antenna_state'].capitalize())
if stash['warnings']:
    atnf['stateError'] = 'warning'
    atnf['errors'] = []
    for key in stash['warnings']:
        atnf['errors'].append({'system': key, 'description':stash['warnings'][key]})
atnf['weather'] = { 'windSpeed': float(stash['weather']['wind_speed_long']), 
                    'temperature': float(stash['weather']['temperature']),
                    'pressure': float(stash['weather']['air_pressure']),
                    'humidity': float(stash['weather']['humidity'])
                  }
if stash['weather']['wind_state'] == 'WIND_OK':
    atnf['weather']['windSpeedError'] = 'ok'
else:
    atnf['weather']['windSpeedError'] = 'bad'

atnf['configuration'] = {'receiver': stash['focus']['receiver']}


print(json.dumps(atnf))


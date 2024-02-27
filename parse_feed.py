#!/usr/bin/python3

# script to fetch the XML (ugh) feed that powers http://ra-state.phys.utas.edu.au/, convert to JSON and publish to local broker
# we may as well wrangle into a known json format, ie https://www.atnf.csiro.au/vlbi/dokuwiki/doku.php/lbaops/jsonmonitoring

# Scope creep will be to add the configuration so that home assistant automatically imports the sensors
# Andrew Elwell, Feb 2024 for https://github.com/Elwell/telescope-tracker

import json
import time
import requests
from xml.etree import ElementTree
from collections import defaultdict
import paho.mqtt.client as mqtt

url = 'http://ra-state.phys.utas.edu.au/cgi-bin/mt_pleasant_26_xml.pl'
#url = 'http://ra-state.phys.utas.edu.au/cgi-bin/ceduna_30_xml.pl'

topic_base = 'telescope-parser'

home_assistant = False ## WIP


print(f'Started Parser, scraping {url}\nPublishing to topic base {topic_base}')

lwt_topic = f'{topic_base}/status'

def on_connect(client, userdata, flags, rc):
	print("Connected to broker with result code "+str(rc))
	client.publish(lwt_topic, payload="online", qos=0, retain=True)

def parse_url(url):
    """"Grab the XML tree from remote site and return as a dict."""
    response = requests.get(url)
    if response.status_code != 200:
        return(None)
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
    return (stash)

def gen_atnf(stash):
    """Output a subset of payload in a standard set of json keys.

    Documentation: https://www.atnf.csiro.au/vlbi/dokuwiki/doku.php/lbaops/jsonmonitoring
    """
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
    return(atnf)
    
def register_ha(client, topic_base):
    """Send Discovery info for Home Assistant.

    Documentation: https://www.home-assistant.io/integrations/mqtt/#configuration-via-mqtt-discovery
    """
    print('Home Assistant integration enabled')
    unique_id = 'scopetracker'
    config_base = f'discovery/binary_sensor/{unique_id}/config'
    disc_payload = { 'origin': {'name': 'Telescope Tracker', 'sw': '0.1.0', 'url': 'https://github.com/Elwell/telescope-tracker'},
                     'state_topic': '{topic_base}/json', 'name': 'Antenna State', 'json_attributes_topic': f'{topic_base}/json',
                     'value_template': '{{ value_json.antenna.antenna_state }}'
                   }


    client.publish(config_base, json.dumps(disc_payload))


mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.will_set(lwt_topic, payload="offline", qos=0, retain=True)
mqttc.connect('192.168.1.4')
mqttc.loop_start()

if home_assistant:
    register_ha(mqttc, topic_base)


while True:
    status = parse_url(url)
    mqttc.publish(f'{topic_base}/hobart_26m/json', json.dumps(status))
    mqttc.publish(f'{topic_base}/atnf_json', json.dumps(gen_atnf(status)))
    time.sleep(3)
mqttc.loop_stop()



from datetime import datetime
import json
import time, os
import re

def config_data(file='setup.json'):
    with open(file, 'r') as setupf:
        data = json.load(setupf)

    setupf.close()
    return data
#function to setup channel playlist relationships from json here
def playlist_w_channel_setup(playlist_channel):
    pc_relationship = {}
    i = 0
    #writes items from json to dict
    for item in playlist_channel:
        pc_relationship[i] = {
            'playlist': item['playlist'],
            'channel': item['channel']
        }
        i += 1
    #returns dict
    return pc_relationship

def time_now():
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    return current_time

def logs(message, log_file = r'logs/default.log', pgrm_signature = __file__):
    pgrm_signature = file_name(pgrm_signature)
    print(message + "signature: " + pgrm_signature)

    now = time_now()

    try:
        with open(log_file, 'a') as f:
            f.write(now + ' - ' + message + " python file: " + pgrm_signature)
            f.write('\n')
    except FileNotFoundError as e:
        print("Please make sure file exists in logs/<your_file_name.log>: "+ str(type(e).__name__))

# Returns the Spotify track or playlist ID from various URL types
def getSpotifyID(url):
    # Regex patterns for regular, uri, and shortened spotify links. AI code.
    patterns = [
        r'open\.spotify\.com/(track|playlist)/([a-zA-Z0-9]+)',
        r'spotify:(track|playlist):([a-zA-Z0-9]+)',
        r'spotify\.link/([a-zA-Z0-9]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            if len(match.groups()) == 2: # if both the content_type and spotify_id
                content_type, spotify_id = match.groups()
            else: # if only spotify
                content_type = None
                spotify_id = match.group(1)

            return {
                'type': content_type,
                'id': spotify_id
            }

    # return none if spotify_ID not found
    return {
        'type': None,
        'id': None
    }

def file_name(file_name = __file__):
    return(os.path.basename(file_name))
import json
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import base64
import supporting_scripts.config_tools as config_tools
import supporting_scripts.channel_tools as channel_tools
import re, datetime


pgrm_signature = "playlist_update.py: "
SECRET_DATABASE = 'setup.json'

async def sendOff(msg, spotify_id): 
    tracks = []

    pgrm_signature = "playlist_update.py: "

    
    config_data = config_tools.config_data(SECRET_DATABASE)
    playlist_channel = (config_data['playlist_channel'])
    init_spotify_flag = config_data['init_spotify_flag']

    # Keep the user from having to get a new token manually every hour
    sp = refresh_sp(init_spotify_flag)

    # Get the playlist link associated with the channel
    playlist_link = channel_tools.return_playlist(sent_channel=msg.channel.id, playlist_channel=playlist_channel)

    # Get the playlist ID
    playlist_ID = config_tools.getSpotifyID(playlist_link)

    tracks.append(spotify_id)

    # add the song to the playlist using the SP object
    sp.playlist_add_items(playlist_ID['id'], tracks)
    config_tools.logs(message=f'{pgrm_signature}: Playlist update {playlist_link} was sent and went through!')
    return f'{pgrm_signature}: Playlist update {playlist_link} was sent and went through!'


def sendOffList(channel, id_list): 
    tracks = []
    pgrm_signature = "playlist_update.py: "

    
    config_data = config_tools.config_data(SECRET_DATABASE)
    playlist_channel = (config_data['playlist_channel'])
    init_spotify_flag = config_data['init_spotify_flag']

    # Keep the user from having to get a new token manually every hour
    sp = refresh_sp(init_spotify_flag)

    # Get the playlist link associated with the channel
    playlist_link = channel_tools.return_playlist(sent_channel=channel, playlist_channel=playlist_channel)
    
    for id in id_list:
        # Get the playlist ID
        playlist_ID = get_playlist_id(playlist_link)

     
        tracks.append(id)

        # add the song to the playlist using the SP object
    sp.playlist_add_items(playlist_ID, tracks)
    config_tools.logs(message=f'{pgrm_signature}: Playlist update {playlist_link} was sent and went through!')
    return f'{pgrm_signature}: Playlist update {playlist_link} was sent and went through!'

# This places in app.py because of the use of spotipy
# Returns the hours of songs in the playlist
def get_playlist_duration(playlist_link):
    # Set up authentication
    playlist_ID = playlist_link.split('/')[-1].split('?')[0]

    # data, TOKEN, refresh_token, expires_at = get_spotify_json() #check out new spotify.json   
    config_data = config_tools.config_data('setup.json')
    init_spotify_flag = config_data['init_spotify_flag']

    sp = refresh_sp(init_spotify_flag)

    # get all tracks from the playlist
    results = sp.playlist_items(playlist_ID)
    tracks = results['items']

    # Get all tracks if there are more than 100 in the playlist
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    # Sum the duration of all songs in miliseconds
    total_duration_ms = sum(track['track']['duration_ms'] for track in tracks if track['track'])

    # Convert milliseconds to hours
    duration_hours = total_duration_ms / (1000 * 60 * 60)
    print(duration_hours)
    return duration_hours


def make_uri(id: str) -> str:
    # Return the URI format
    return f"spotify:track:{id}"

def return_song_id(link: str) -> str:
    # Split by ':' to get the part after 'spotify:track:'
    track_id = link.split(':')[-1]
    # Split by '?' to remove any query parameters and keep only the ID
    track_id = track_id.split('?')[0]
    return track_id

def get_playlist_id(playlist_link):
    fline = playlist_link.replace("https://open.spotify.com/playlist/", "")#deletes first part of the link
    PLAYLISTID = fline.split("?", 1)[0]
    return PLAYLISTID

#loads cache file into spotify json
def cache_2_json(init_spotify_token_flag):
    if(str(init_spotify_token_flag).upper() == 'TRUE'): #If true meaning the spotify.json file has never been populated before
        open('spotify.json', 'w+').close() #clears old token info if there is any

        file1 = open("spotify.json", "a") #prepares file to be written to 

        file2 = open(".cache", "r+")#reads the cached file 
        rline2 = file2.readlines()
        for line in rline2:
            content = line
            
            config_tools.logs(message="Wrote info from .cache -> spotify.json " , log_file=r'logs/error.log')

            file1.write(content)#writes the content into the json file
        
        #update setup.json and flip flag back to false so this function only runs once, when the program is first installed ideally, can be fliped to true for debugging and a sure fire way to revie spotbot if .cache exists
        
            with open("setup.json", "r") as jsonFile:
                data = json.load(jsonFile)

            data["init_spotify_flag"] = False

            with open("setup.json", "w") as jsonFile:
                json.dump(data, jsonFile, indent=4)
        
        config_tools.logs(message="Updated use_init_spotify_token' in setup.json and set it from True -> False ", log_file=r'logs/error.log')
        
        file1.close()
        jsonFile.close()

def verify_spotify_json_integrity():
    file_path = r"spotify.json"
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        config_tools.logs(message="Error with loading Spotify.Json: " + str(e), log_file=r'logs/error.log')
    
    expected_keys = ["access_token", "token_type", "expires_in", "scope", "expires_at", "refresh_token"]
    for key in expected_keys:
        if data.get(key) is None:
            print(f"Error: Key '{key}' is missing from the JSON file.")
        elif data.get(key) != 1:
            print(f"Error: Key '{key}' has multiple values in the JSON file.")
    
    print("JSON file is valid.")

def calculate_expires_at(unix_time):
    return int(time.time() + unix_time)

def spotify_json_update(refresh_data):
    with open("spotify.json", 'r') as info: #reads the json file that was just written to 
        data = json.load(info)
        refresh_token = (data['refresh_token'])
        access_token = refresh_data['access_token']
        scope = (data['scope'])
    info.close()

    token_type= refresh_data['token_type']
    expires_in = refresh_data['expires_in']
    expires_at = calculate_expires_at(unix_time=expires_in) #gets when token will expire
    expires_at = expires_at #formats to unix time

    #json data that will always be in the spotify token, update the values that need to be updated from refresh_data, and maintain all info from spotify.json that should be kept
    json_data = {
        "access_token" : access_token,
        "token_type": token_type,
        "expires_in": expires_in,
        "scope": scope,
        "expires_at": expires_at,
        "refresh_token" : refresh_token
    }

    with open(r'spotify.json', 'w') as f:
        f.truncate()  # Clear the file before the write
        json.dump(json_data, f, indent=4) #writes the data that we keep from the OG json file & then put the new token info we will use for the next hr in there

    config_tools.logs("spotify.json updated", log_file=r'logs/token_info.log')

def is_unix_time_in_past(unix_time):
    now = datetime.datetime.now(datetime.timezone.utc)
    now_unix = int(now.timestamp())
    return unix_time < now_unix

def refresh_the_token(client_id, client_secret):
    pgrm_signature = "playlist_update.py: "
    with open("spotify.json", 'r') as info: #reads the json file that was just written to 
        data = json.load(info)
        refresh_token = (data['refresh_token'])
            #This code was made possible by https://www.youtube.com/watch?v=-FsFT6OwE1A 
            #Notable timestamps 10:14, 40:25

        #check to see if token has past

        auth_client = client_id + ":" + client_secret
        auth_encode = 'Basic ' + base64.b64encode(auth_client.encode()).decode()

        headers = {
            'Authorization': auth_encode,
            }

        data = {
            'grant_type' : 'refresh_token',
            'refresh_token' : refresh_token
            }

        response = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers) #sends request off to spotify

        if(response.status_code == 200): #checks if request was valid
            print(pgrm_signature + "The request to went through we got a status 200; Spotify token refreshed")
            response_json = response.json()
            new_expire = response_json['expires_in']
            print(pgrm_signature + "the time left on new token is: "+ str(new_expire / 60) + "min") #says how long
            return response_json
        else:
            config_tools.logs("ERROR! when attempting to run refresh_the_token()! The response we got was: "+ str(response))
            print(pgrm_signature + "ERROR! The response we got was: "+ str(response))
            return
            # return TOKEN #last ditch to try and make it work if TOKEN varaible is still active


def refresh_sp(init_spotify_flag): 
    #get default config data
    config_data = config_tools.config_data('setup.json')
    client_id = (config_data['client_id'])
    client_secret = (config_data['client_secret'])
    

    #gets spotify.json data
    if(str(init_spotify_flag).upper() == "FALSE"):
        with open("spotify.json", 'r') as info: #reads the json file that was just written to 
            data = json.load(info)
            expires_in = (data['expires_in'])
            expires_at = (data['expires_at'])
            TOKEN = (data['access_token'])
    else:
        #if the init spotify flag has not be set to true yet, have the .cache file write to spotify.json
        cache_2_json(init_spotify_token_flag=init_spotify_flag) #call this in the spotbot.py file main need to improve token
        with open("spotify.json", 'r') as info: #reads the json file that was just written to 
            data = json.load(info)
            expires_in = (data['expires_in'])
            expires_at = (data['expires_at'])
            TOKEN = (data['access_token'])
    #converts our .cache file to a json for easier processing, have part of the code set this to false after first time
    
    now = int(time.time())#gets the current time 
    #dealing with unix time for now & expires in
    math = now - expires_at
    is_expried = (math >= (expires_in - 200)) #checks to see if the time now is greater than or less to 60min slightly 120 less than the 60 sec mark

    time_left = (math * -1) #finds out how much time is left on the token

    print(pgrm_signature + "the time left on the token is: "+ str(time_left / 60) + "min")
    
    if(int(time_left) < 2): #if token is 2 min away from expiring
        refreshed_info = refresh_the_token(client_id=client_id, client_secret=client_secret)
        spotify_json_update(refresh_data=refreshed_info) #updates spotify.json
        sp = spotipy.Spotify(auth=refreshed_info['access_token']) #Places the new refreshed token into the app
    else:
        sp = spotipy.Spotify(auth=TOKEN) #creates object that interacts with spotify api; uses the first token generated; token only last 1 hour

    #return refreshed spotipy object
    return sp

#extracts a song from a message object
def song_link_extract(msg):
    # Regular expression to match Spotify links
    pattern = r"https://open.spotify.com/track/[\w\d]+"
    
    # Search for the pattern in the provided text
    match = re.search(pattern, msg.content)
    # Return the matched link if found, otherwise None
    song = match.group(0) if match else None
    
    return song

def get_track_name_and_artist(trackID):

    config_data = config_tools.config_data('setup.json')
    init_spotify_flag = config_data['init_spotify_flag']

    sp = refresh_sp(init_spotify_flag)

    now = int(time.time())#gets the current time

    track = sp.track(trackID)
    artists = track['artists']
    # {track['artists']['name']

    return [str(track['name']), str(artists[0]['name'])] # Index 0 is title, index 1 is artist. This allows the caller to
                                                         # customize their output however they choose.
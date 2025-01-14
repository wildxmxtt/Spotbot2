from discord.ext import commands
import re
import sqlite3
import discord
from datetime import datetime
import json
import playlist_update
from os import path
import random
import calendar
import achievements
import aiohttp
import io
import database_tools
import supporting_scripts.config_tools as config_tools
import supporting_scripts.channel_tools as channel_tools
import time
pgrm_signature = "spotbot.py: "

# Define the setup JSON
SECRET_DATABASE = 'setup.json'
# Sets up our secret information into the application from secrets.db
config_data = config_tools.config_data(SECRET_DATABASE)
CLIENT_ID = config_data['client_id']
CLIENT_SECRET = config_data['client_secret']
TOKEN = config_data['discord_token']
grab_past_flag = config_data['grab_past_flag']
LEADERBOARD = config_data['installed_features']['leaderboard']
PLAYLIST_CHANNEL = config_data['playlist_channel']


intents = discord.Intents.all()
intents.members = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)


@bot.event
async def on_ready(bot=bot):
    check_past_ran = False
    config_data = config_tools.config_data(SECRET_DATABASE)
    check_past_on_boot = config_data['check_past_on_boot']
    #Lets programmer know that the bot has been activated
    print(pgrm_signature + 'SpotifyBot: ON')
    
    if str(check_past_on_boot).upper() == 'TRUE' and check_past_ran == False:
        for channel_item in config_data['playlist_channel']:
            channel = int(channel_item['channel'])
            channel_ctx = bot.get_channel(channel)
            if channel_ctx is not None:
                    await channel_ctx.send("Bot is now online! Validating messages, DO NOT SEND ANY COMMANDS TO SPOTBOT DURING THIS TIME UNTIL COMPLETE MESSAGE IS SENT!")  # Message to send on startup
                    songs = await search_past(enabled=True, ctx=channel_ctx, channel=channel, bot=bot)
                    await channel_ctx.send("COMPLETE: Validated lost songs! Songs added from channel was: " + str(len(songs)))  # Message to send on startup
                    check_past_ran = True
            else:
                print("Channel not found. Please check the channel | ID:" + channel)



#This is the help command that lets the user know all of the avaliable commands that can be used 
@bot.command()
async def hlp(ctx):
    helpText = ("The commands for this bot go as follows: \n" + 
        "[!]sLink (gives the user the link to the spotify playlist that the channel is associated with) \n" + 
        "[!]sLinkAll (gives the user the all of the links to the spotify playlists that spotbot is associated with) \n" + 
        "[!]grabPast (allows for the user to grab past songs sent in a chat, this can only be ran once) \n" +
        "[!]r (gives the user a random song from the playlist!) \n" +
        "[!]search (checks if a given spotify link has been added to the playlist) \n" +
        "[!]waves (generate Spotify's wave codes png image files.)\n")

    if LEADERBOARD is True:
        helpText += ("[!]leaderboard (gives a leadearboard of all time highest contributing users) \n" +
            "[!]thismonth (gives a leaderboard of this months hightst contributing users) \n" +
            "[!]reactchamp (gives a leaderboard of this months most reacted contributed songs) \n" +
            "[!]localreactchamp (gives a leaderboard of this months most reacted contributed songs)")

    await ctx.reply(helpText +
            "\n\nWhen a user sends a messsage in this chat the bot will analyze that message, if it is a valid spotify link it will be placed into the playlist\n")
    

#gives the link set in the setup.json file
@bot.command()
async def sLink(ctx):
    config_data = config_tools.config_data('setup.json')
    channel_ID = int(ctx.channel.id)
    channel = bot.get_channel(channel_ID)
    config_data = config_tools.config_data(SECRET_DATABASE)
    playlist_channel = config_data['playlist_channel']
    playlist_link = channel_tools.return_playlist_from_channel(sent_channel=ctx.channel.id, playlist_channel=playlist_channel)
    #playlist_links = await channel_tools.return_playlists(playlist_channel=playlist_channel)
    await ctx.reply(f"**{str(channel.name)}'s** playlist is:\n\n{playlist_link}")

@bot.command()
async def search(ctx, arg = None):
    # Begin input validation
    spotify_link = str(arg)
    idInformation = config_tools.getSpotifyID(spotify_link)

    song_id = idInformation['id']

    if arg == None:
        await ctx.reply("Please provide an argument for this command.")
        return
    elif id == None:
        await ctx.reply("Please provide a valid Spotify link as an argument.\n```Examples:\nhttps://open.spotify.com/track/foo\nhttps://open.spotify.com/track/foo?si=bar```")
        return
    # End input validation

    # Begin song ID extraction
    name_and_artist = playlist_update.get_track_name_and_artist(song_id)
    song_id_wildcard = "%" + song_id + "%"
    # End song ID extraction
    
    # Get current configured playlist for the Discord channel
    playlist_link = channel_tools.return_playlist(sent_channel=ctx.channel.id, playlist_channel=PLAYLIST_CHANNEL)
    playlist_id = config_tools.getSpotifyID(playlist_link)['id']
    # End playlist ID extraction

    # Begin SQLite query
    conn = sqlite3.connect('databases/spotbot.db')
    cur = conn.cursor()

    # Return all message IDs to find sender ID
    cur.execute("""
        SELECT discord_message_id
        FROM songs
        WHERE spotify_ID LIKE ? AND playlist_ID = ?;
        """, (song_id_wildcard, playlist_id,))
    message_id = cur.fetchone()
    # End SQLite query

    # Begin message search
    if message_id != None:
        current_channel = ctx.channel.id
        channel = bot.get_channel(current_channel)
        if channel == None:
            await ctx.reply("Channel not found.")
            return
        try:
            message = await channel.fetch_message(message_id[0])
            result = f"Song found!\n\n**Title:** {name_and_artist[0]}\n**Artist:** {name_and_artist[1]}"
            await message.reply(result)
        except:
            await ctx.reply(f"The provided song exists in the playlist, but cannot be found in the current channel.\n\n**Title:** {name_and_artist[0]}\n**Artist:** {name_and_artist[1]}")
    else:
        await ctx.reply("The provided song does not exist in the playlist.")
    # End message search

@bot.command()
async def sLinkAll(ctx):
    config_data = config_tools.config_data(SECRET_DATABASE)
    playlist_channel = config_data['playlist_channel']

    links = "**All** Playlists:\n"
    for item in playlist_channel:
        try:
            channel = bot.get_channel(int(item['channel']))
            links += f"\n**{str(channel.name)}**: {str(item['playlist'])}"
        except KeyError as e:
            print(f"Error! No playlist links found: {e}")
            await ctx.reply(f"No playlist links found.")
            return None
        except Exception as e:
            print(f"Error! An exception has occured: {e}")
            await ctx.reply("An error has occured.")

    await ctx.reply(links)


#a request command to give the user back a random song from the playlist 
@bot.command()
async def r(ctx): 
    # Connect to the SQLite Database
    conn = sqlite3.connect('databases/spotbot.db')
    cur = conn.cursor()

    # Get the number of total songs in the playlist
    cur.execute('SELECT COUNT(*) FROM songs')
    count = cur.fetchone()[0]

    print(f"There are {count} song IDs in the songs table.")

    # Get all spotify_IDs from the songs table
    cur.execute('SELECT spotify_ID FROM songs')
    spotify_ids = [row[0] for row in cur.fetchall()]

    # if there are songs
    if spotify_ids:
        # get a random id
        random_song = random.choice(spotify_ids)
        link = f"https://open.spotify.com/track/{random_song}"
        print(f"The random song you got was: {link}")
        await ctx.reply(f"The random song you got was: {link}")
    else: # if there are no songs
        print(f"There are no songs yet.")
        await ctx.reply("There are no songs yet. A random song cannot be retrieved.")

    # Close the connection
    conn.close()

# a request command to produce an all time leaderboard stats for the respective discord server 
@bot.command()
async def leaderboard(ctx):
    # Check if the leaderboard information is enabled via setup.json
    if LEADERBOARD == 0: return False

    # Connect to the SQLite Database
    conn = sqlite3.connect('databases/spotbot.db')
    cur = conn.cursor()

    # Get top 10 users and their number of songs added
    cur.execute("""
        SELECT sender_ID, COUNT(*) as song_count
        FROM songs
        GROUP BY sender_ID
        ORDER BY song_count DESC
    """)

    # Fetch all
    results = cur.fetchall()

    # Send the embed
    title="All Time Leaderboard"
    await sendLeaderBoardEmbed(ctx, results, title)

    # Close the connection
    conn.close()

# a request command to produce a leaderboard with this months stats for the respective discord server
@bot.command()
async def thismonth(ctx):
    # Check if the leaderboard information is enabled via setup.json
    if LEADERBOARD == 0: return False

    # Connect to the SQLite Database
    conn = sqlite3.connect('databases/spotbot.db')
    cur = conn.cursor()

    # Get the current year and month
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    # Get top 10 users and their number of songs added for the current month
    cur.execute("""
        SELECT sender_ID, COUNT(*) as song_count
        FROM songs
        WHERE strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ?
        GROUP BY sender_ID
        ORDER BY song_count DESC
        LIMIT 10
    """, (str(current_year), f"{current_month:02d}"))

    # Fetch all
    results = cur.fetchall()

    # Send the embed
    title="This Months Stats"
    await sendLeaderBoardEmbed(ctx, results, title)

    # Close the connection
    conn.close()

# A request that produces a leaderboard with this months highest reacted songs
@bot.command()
async def reactChamp(ctx):
    # Check if the leaderboard information is enabled via setup.json
    if LEADERBOARD == 0: return False

    # warn user this may take a while
    await ctx.send(f"Grabbing messages - this may take a while...")

    # Connect to SQLite Database
    conn = sqlite3.connect('databases/spotbot.db') # create or connect to the database
    cur = conn.cursor()

    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    # Get top 10 users and their number of songs added for the current month
    cur.execute("""
        SELECT spotify_id, discord_message_id, sender_ID
        FROM songs
        WHERE strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ?
    """, (str(current_year), f"{current_month:02d}"))

    message_ids = cur.fetchall()

    messages = []
    # loop through each message ID
    for msg_id in message_ids:
        try:
            message = await ctx.channel.fetch_message(msg_id[1])                        # Grab each message
            total_reactions = sum(reaction.count for reaction in message.reactions)     # grab the total amount of reacitons for respective message
            if total_reactions > 1:
                messages.append((message, total_reactions-1, msg_id[0], msg_id[2]))       # Add tuple of message, total reactions, and the spotify link
        except discord.NotFound:
            print(f"{pgrm_signature}: Message with ID {msg_id[1]} not found")
        except discord.Forbidden:
            print(f"{pgrm_signature}: Bot doesn't have permission to fetch message {msg_id[0]}")
        except discord.HTTPException:
            print(f"Failed to fetch message {msg_id[1]}")

    # Sort the results
    # sorted is fed messages, key=lambda (idk why), x[1] for the reaction count, 
    # and reverse true for descending orde. [:5] to get the top 5
    top_messages = sorted(messages, key=lambda x: x[1], reverse=True)[:5]

    # make and send the embed
    title = f"Reaction Champions for {calendar.month_name[current_month]}"
    embed = discord.Embed(title=title, color=0x1DB954)
    embed.description = "The top 5 highest reacted songs this month"

    loops = 1
    guild = ctx.guild
    for message in top_messages:
        # Get username
        member = guild.get_member(message[3])

        # Get track name and artist(s)
        nameAndArtist = playlist_update.get_track_name_and_artist(message[2])

        field_value = f"{message[1]} reaction(s) - "

        field_value += f"[{nameAndArtist[0]} - {nameAndArtist[1]}](https://open.spotify.com/track/{message[2]})"

        embed.add_field(name=f"{loops}. {member.display_name}", value=field_value, inline=False)
        loops += 1

    await ctx.send(embed=embed)

    conn.close()

# A request that produces a leaderboard with this months hight reacted songs local to the represented playlist
@bot.command()
async def localreactChamp(ctx):
    # Check if the leaderboard information is enabled via setup.json
    if LEADERBOARD == False: return False

    for playlist in PLAYLIST_CHANNEL:
        if ctx.channel.id == int(playlist['channel']):
            # warn user this may take a while
            await ctx.send(f"Grabbing messages - this may take a while...")

            # Connect to SQLite Database
            conn = sqlite3.connect('databases/spotbot.db')
            cur = conn.cursor()

            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month

            playlist_ID = config_tools.getSpotifyID(playlist['playlist'])['id'] #FIX THIS

            # Get top 10 users and their number of songs added for the current month for the specified playlist
            cur.execute("""
                SELECT spotify_id, discord_message_id, sender_ID
                FROM songs
                WHERE strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ? AND playlist_ID = ?
            """, (str(current_year), f"{current_month:02d}", playlist_ID,))

            message_ids = cur.fetchall()

            messages = []
            # loop through each message ID
            for msg_id in message_ids:
                try:
                    message = await ctx.channel.fetch_message(msg_id[1])                        # Grab each message
                    total_reactions = sum(reaction.count for reaction in message.reactions)     # grab the total amount of reacitons for respective message
                    if total_reactions > 1:
                        messages.append((message, total_reactions-1, msg_id[0], msg_id[2]))       # Add tuple of message, total reactions, and the spotify link
                except discord.NotFound:
                    print(f"{pgrm_signature}: Message with ID {msg_id[1]} not found")
                except discord.Forbidden:
                    print(f"{pgrm_signature}: Bot doesn't have permission to fetch message {msg_id[0]}")
                except discord.HTTPException:
                    print(f"Failed to fetch message {msg_id[1]}")

            # Sort the results
            # sorted is fed messages, key=lambda (idk why), x[1] for the reaction count, 
            # and reverse true for descending orde. [:5] to get the top 5
            top_messages = sorted(messages, key=lambda x: x[1], reverse=True)[:5]

            # make and send the embed
            title = f"Reaction Champions for {calendar.month_name[current_month]}"
            embed = discord.Embed(title=title, color=0x1DB954, url=playlist['playlist'])
            embed.description = "The top 5 highest reacted songs this month"

            loops = 1
            guild = ctx.guild
            for message in top_messages:
                # Get username
                member = guild.get_member(message[3])

                # Get track name and artist(s)
                nameAndArtist = playlist_update.get_track_name_and_artist(message[2])

                field_value = f"{message[1]} reaction(s) - "

                field_value += f"[{nameAndArtist[0]} - {nameAndArtist[1]}](https://open.spotify.com/track/{message[2]})"

                embed.add_field(name=f"{loops}. {member.display_name}", value=field_value, inline=False)
                loops += 1

            await ctx.send(embed=embed)

            conn.close()

# Using the result from an SQL querey, an embed is created and sent
async def sendLeaderBoardEmbed(ctx, results, title):
    userIDs = [row[0] for row in results]
    usernames = {}
    guild = ctx.guild
    # For each user ID in the results get the username
    for userID in userIDs:
        try:
            member = guild.get_member(userID)
            if member is None:
                print(f"Debug: Fetching member {userID}")
                member = await guild.fetch_member(userID)
            
            # Attempt to get the display name, if not available get the name
            if member.display_name:
                usernames[userID] = member.display_name
            else:
                usernames[userID] = member.name

        except discord.NotFound:
            usernames[userID] = "Unknown User"

    # Create the embed
    embed = discord.Embed(title=title, color=0x1DB954)
    embed.description = "The top 10 users who have sent the most songs:"

    loops = 1

    for row in results:
        if loops != 10:
            discord_id, song_count = row
            username = usernames.get(discord_id, "Unknown")
            
            # Add the new information to the response
            # response += (f"\n{username:8s} | {song_count:15d}")
            embed.add_field(name=f"{loops}. {username}", value=f"{song_count} songs", inline=False)
            loops += 1
        else:
            # Only print the first 10
            break

    await ctx.send(embed=embed)

#This is to grab the past songs that have been sent to the channel
@bot.command()
async def grabPast(ctx):
    channel_id = ctx.channel.id
    await ctx.reply("Grabbing songs now please wait until FINISHED is sent\nGrabbing & Flitering Past Messages (this could take a while).....")                

    pastSongMsgList = await search_past(bot=bot, ctx=ctx, enabled=True, channel=channel_id)

    # send a success after the loop
    await ctx.send("Messages Grabbed, Process Complete, FINISHED: " + str(len(pastSongMsgList)) +" new songs were found with grabPast" + "\nHere is the Spotify Link: ")
    await sLink(ctx)
        
    update_gp_flag()
    print(f"{pgrm_signature}: Updated the grabpast flag")
        


@bot.event
async def on_message(msg):
    config_data = config_tools.config_data(SECRET_DATABASE)
    grab_past_flag = config_data['grab_past_flag']
    
    #gets channels from playlist channel
    channels = await channel_tools.return_channels(playlist_channel=PLAYLIST_CHANNEL)

    #checks if message was sent in a channel spotbot is tracking
    valid_channel_flag = await channel_tools.is_message_in_valid_channel(message=msg, channels=channels)
    
    if(valid_channel_flag == True):

        # Get the link info
        link_info = config_tools.getSpotifyID(msg.content)

        spotify_id = link_info['id']
        content_type = link_info['type']
        msg_valid = channel_tools.msg_validity_check(msg, bot)
        content_type = None #sets contnet type to none to start
        if(msg_valid):
            # If the ID is present in the message and the link is for a track
            if spotify_id and content_type != 'playlist':
                # Loop through available playlists
                for playlist in PLAYLIST_CHANNEL:
                    # If the link is sent into the chat specified
                    if msg.channel.id == int(playlist['channel']):
                        if not "The random song you got was:" in str(msg.content) and not "!search" in str(msg.content) and not "!waves" in str(msg.content): # Without this it would catch all songs comand as a new link for some reason.
                            print(pgrm_signature + "Valid Spotify Link")

                            checkEmoji = "☑️"
                            rEmoji = "🔁" 

                            #get the correct playlist link associated with the channel
                            playlist_link = channel_tools.return_playlist_from_channel(sent_channel=msg.channel.id, playlist_channel=PLAYLIST_CHANNEL)
                            # Check to see if the song is duplicate, if not add it to the DB
                            test = dupCheck(msg, spotify_id, playlist_link)

                            # Decides what emoji to add based on if it is a duplicate or not
                            if(test == True):
                                await channel_tools.addEmoji(emoji=rEmoji, msg=msg) #if song is a repeat put a repeat emoji on it
                            else:
                                # Once added to DB send to spotify to add to playlist
                                print(f"{await playlist_update.sendOff(msg=msg, spotify_id=spotify_id)}")
                                await channel_tools.addEmoji(emoji=checkEmoji, msg=msg) #if song is a repeat put a repeat emoji on it

                                # Warn users that previous songs may not be accounted for as grabPast has NOT been called
                                if(int(grab_past_flag) == 0):
                                    await msg.reply("WARNING GRAB PAST FLAG IS STILL ZERO, IF THERE ARE NO PAST SONGS YOU NEED TO GRAB. SET THE GRAB PAST FLAG TO ZERO IN setup.json AND RESTART spotbot.py. THIS WILL CAUSE ERRORS ELSEWISE")
                                
                                # Check for acheivements (connect to db, get song count)
                                conn = sqlite3.connect('databases/spotbot.db')
                                cur = conn.cursor()

                                cur.execute("SELECT COUNT(*) FROM songs WHERE playlist_ID = ?", (config_tools.getSpotifyID(playlist_link)['id'],))
                                songs = cur.fetchone()[0]

                                # Every 10 songs check for achievements (For perfromance)
                                if (songs % 5 == 0 or songs == 69):
                                    # Get the acheivement string (if any)
                                    celebration = achievements.checkAchievement(songs, grab_past_flag)

                                    # Get duration achievement (if any)
                                    duration = achievements.checkDurationAchievement(playlist_update.get_playlist_duration(playlist_link))

                                    # If there is a celebration, send the message
                                    if(celebration):
                                        await msg.channel.send(celebration)
                                    if(duration):
                                        await msg.channel.send(duration)
                                
                                conn.close()


        else:
            print(pgrm_signature + "Not valid Spotify channel or spotify link in: " + str(msg.channel.id) + " | spotbot looking at channels: " + str(channels))
            await bot.process_commands(msg)


@bot.command()
async def waves(ctx, arg = None):
    if(arg == None):
        await ctx.reply('User Must provide a spotify link argument for this command to work')
        return
    for playlist in PLAYLIST_CHANNEL:
        # Command only functions within the global variable: discord_channel, specified in setup.json
        if ctx.channel.id == int(playlist['channel']):
            try:
                # Regex to ensure argument passed to command is acceptable
                wave_uri = config_tools.getSpotifyID(arg)['id']
                # Format URL string for async request
                wave_url = 'https://scannables.scdn.co/uri/plain/png/000000/white/640/spotify:track:%s' % (wave_uri)
                # Async request for a response from variable: wave_url
                async with aiohttp.ClientSession() as wave_session:
                    async with wave_session.get(wave_url) as wave_resp:
                        # Catch "unsuccessful" (not 200) response status
                        if wave_resp.status != 200:
                            return await ctx.send('Wavecode not found')
                        wave_img = io.BytesIO(await wave_resp.read())
                # Sends image structured in Bytes as a discord.File in the channel
                await ctx.send(file=discord.File(wave_img, '%s_wavecode.png' % (wave_uri)))

            # Catching unexpected errors
            except Exception as err:
                print(pgrm_signature + "Error occurred -> %s" % err)
                config_tools.logs(message="Error occurred -> %s" % err, log_file=r'logs/error.log')
                await ctx.reply('Error occured please check log files on spotbot server')

async def fetch_message_history(channel_ID):
    channel = bot.get_channel(channel_ID)
    if channel is None:
        print(f"Channel with ID {channel} not found.")
        try:
            channel = await bot.fetch_channel(channel_ID)
        except discord.errors.NotFound:
            print(f"Channel with ID {channel_ID} does not exist.")
        except discord.errors.Forbidden:
            print(f"Bot does not hav epermission to acces channel{channel_ID}")
    
    print(f"Channel found: {channel.name} (ID: {channel_ID}, Type: {type(channel)})")

    if not isinstance(channel, discord.TextChannel):
        print(f"Channel {channel_ID} is not a text channel.")
    
    try:
        messages = [message async for message in channel.history(limit=500000)]
        print(f"Successfully fetched {len(messages)} messages from channel {channel.id}")
    except discord.errors.Forbidden:
        print(f"Bot doesn't have permission to read message history in channel {channel.id}")
    except Exception as e:
        print(f"An error occurred while fetching history for channel {channel.id}: {e}")

    return messages

async def search_past(ctx, bot, enabled=False, channel=""):
    checkEmoji = "☑️"
    rEmoji = "🔁" 

    #if search past is being ran on startup, then channel will be ""
    if(channel == ""):
        channel_ID = ctx.last_message.channel.id
    else: #if search_past is called by grabpast then set the channel to the channel ID
        channel_ID = channel


    if(enabled == True):
        config_tools.logs("Grabbing past messages.....", log_file=r'logs/channel_tools.log')
        messages = await fetch_message_history(channel_ID=channel_ID)
        # messages = [messages async for messages in ctx.history(limit=500000)] #If your bot is not reading all of your messages this number may have to be higher 500000

        # to make it work with only one file, surprisingly all the playlist file handling is done in dupCheck()
        raw_track_list = []
        for msg in messages:
            try:
                #checks if message is valid before proceding
                msg_valid = channel_tools.msg_validity_check(msg, bot)
                content_type = None #sets contnet type to none to start
                if(msg_valid):
                    # Get the link info
                    link_info = config_tools.getSpotifyID(msg.content)
                    content_type = link_info['type']
                    spotify_id = link_info['id']

                    # ignore playlists and non spotify links
                    if content_type == 'track':
                        # Get the playlist link associate with the channel
                        playlist_link = channel_tools.return_playlist_from_channel(sent_channel=msg.channel.id, playlist_channel=PLAYLIST_CHANNEL)
                        check = dupCheck(msg, spotify_id, playlist_link, autoAdd2DB=True) #checks to see if the correct emoji is on the message, SWITCH TO FALSE WHEN re-write is made && songs are added to db AFTER added to playlist
                    
                        # If the song is not a duplicate, add song to the raw_track_list to be sent off
                        if check == False:
                            raw_track_list.append(spotify_id)      
                            #need a re-write of this to make it to where emojis are only placed on a song, after it has been added to playlist worry about this later for now 1/7/2025 - MattW
                            if(await channel_tools.emojiCheck(msg) == False):#check to see if message needs an emoji or not
                                await channel_tools.addEmoji(emoji=checkEmoji, msg=msg) #if song is a repeat put a repeat emoji on it
                            else:
                                await channel_tools.addEmoji(emoji=rEmoji, msg=msg) #if song is new put a check emoji on it
                                
            except discord.NotFound:
                config_tools.logs(message=f"{pgrm_signature}: Message with ID {msg.id} not found", log_file=r'logs/error.log')
            except discord.Forbidden:
                config_tools.logs(message=f"{pgrm_signature}:  Bot doesn't have permission to fetch message {msg.id}", log_file=r'logs/error.log')
            except discord.HTTPException:
                config_tools.logs(message=f"{pgrm_signature}: Failed to fetch message {msg.id}", log_file=r'logs/error.log')
            except Exception as e:
                config_tools.logs(message="Error whilst checking for duplicate: " + str(e), log_file=r'logs/error.log')

        #check to see if every song in the batch list is valid. If there is one false thrown, add songs one at a time & let send off fail for those songs
        results = config_tools.validate_spotify_uris(uri_list=raw_track_list)

        if(False in results):
            i = 0
            #send off songs one at a time if there was a false thrown, let the songs that were false fail. (This is done to ensre if we got a false positve those songs are still uploaded)
            for spotify_id in raw_track_list:
                #set a sleep here for 20 seconds every time an increment of 50 is hit to prevent spotify ratelimit
                try:
                    i = i + 1
                    await playlist_update.sendOff(msg=msg, spotify_id=spotify_id, tracks=None, batch_send=False)
                except Exception as e:
                    config_tools.logs(message="Error when sending song off to spotify: " + str(e), log_file=r'logs/error.log')
                if(i % 50 == 0):
                    await ctx.send("Awaiting for 20 seconds to prevent spotify rate limit, happens for every 50 songs sent to spotify that were not all sent at once")
                    time.sleep(20) #sleep for 20 seconds after songs have been added to aviod rate limit
                    await ctx.send("continuting to add songs sleep, over")
        else: 
            #send off the batch of songs 50 at a time, if the track list is not empty
            master_track_list = []
            #generate a list of lists (aka master track list), if the list is greater than 50 
            if(len(raw_track_list) < 50):
                master_track_list = config_tools.split_large_list(input_list = raw_track_list)
            else:
                master_track_list.append(raw_track_list)

            #go through each track_list in master track list
            for track_list in master_track_list:
                if(track_list != []):
                    try:
                        await playlist_update.sendOff(msg=msg, spotify_id=None, tracks=track_list, batch_send=True)
                    except Exception as e:
                        config_tools.logs(message="Error when sending song off to spotify: " + str(e), log_file=r'logs/error.log')
        
        # This is here to only add songs AFTER the songs have been added to the playlist; Opening a ticket for now as tokenization issues are far more importiant 1/7/2025 - MattW
        # songlink = playlist_update.song_link_extract(msg)
        # database_tools.add_song_2_db(msg=msg, songlink=songlink)

        config_tools.logs("Grabbed past messages", log_file=r'logs/channel_tools.log')
        print("Past finished searching for channel " + str(channel))
        return raw_track_list

#checks for duplicates before sending songs off to uri.txt and recording in database
def dupCheck(msg, spotify_id, playlist_link, autoAdd2DB = True):
    songlink = playlist_update.song_link_extract(msg)
    
    # opening a text files (new)
    conn = sqlite3.connect('databases/spotbot.db')
    cur = conn.cursor()

    # Attempt to select spotify_ID
    # input sanitization - https://realpython.com/prevent-python-sql-injection/
    # Check if there is a song id in the specified playlist
    playlist_ID = config_tools.getSpotifyID(playlist_link)['id']
    cur.execute("SELECT spotify_ID FROM songs WHERE spotify_ID = ? AND playlist_ID = ? LIMIT 1", (spotify_id,playlist_ID,))
    matches = cur.fetchone()

    # If a match is found
    if matches:
        print(f'{pgrm_signature}: Song {songlink} found In song database')

        # EXIT and return true; this is infact a duplicate
        return True
    else: # If a match is not found
        # Add the song ID into the database
        if(autoAdd2DB == True):
            print(pgrm_signature + 'NEW! | String', songlink , 'Not Found')
            cur.execute("INSERT INTO songs (spotify_ID, playlist_ID, sender_ID, timestamp, discord_message_id) VALUES (?, ?, ?, ?, ?)", 
                        (spotify_id, playlist_ID, getSender(msg), getTimestamp(msg), getMessageID(msg)))
            conn.commit()
            
            conn.close()
            return False




def uritxt(link):
    config_data = config_tools.config_data()
    grab_past_flag = config_data['grab_past_flag']

    print(pgrm_signature + "Writting to uri.txt..... \n")
    
    # Ensure the link is computed as a str
    song = str(link)

    if(grab_past_flag == 0):
        # new code
        print("WARNING GRAB PAST FLAG IS SET TO ZERO, MAKE SURE THIS IS SET TO 1 IF YOU DONT HAVE ANY SONGS YOU NEED TO GET FROM THE PAST")
        print(pgrm_signature + "Writting to uri.txt.....: \n")

        # connect to the database
        conn = sqlite3.connect('databases/spotbot.db')
        cur = conn.cursor()

        # Select all spotify IDs
        cur.execute("Select spotify_ID FROM songs")
        rline = cur.fetchall() # retreive all spotify IDs and store in readlines

        # Prepare to write the spotify IDs to the uri.txt file
        file1 = open("uri.txt", "a")
    
        # Loop through each spotify ID
        for line in rline:
            # Convert tuple to string if necessary, sometimes we receive a string
            if isinstance(line, tuple):
                line = line[0] # Take the first element of the tuple (spotifyID)

            # Adds expected format to begingin of the spotify ID and writes to the file
            formattedLine = line.replace("https://open.spotify.com/track/", "spotify:track:")

            # Cuts off exess info from the uri and writes it to the file
            file1.write(formattedLine.split("?si")[0] + "\n")

        # Send status, close the connection and file
        print(pgrm_signature + "uri.txt has been written to")
        file1.close()
        conn.close()
        
    else:
        file1 = open("uri.txt", "w+")

        # Changing to the format expected
        formattedLine = song.replace("https://open.spotify.com/track/", "spotify:track:")
        formattedLine = formattedLine.split("?", 1)[0] # removing all contents regarding session ID
        
        # Writes URI to the file
        file1.write(formattedLine + "\n")
        print(f"These have been written to the uri.txt file")

        file1.close()
    
def update_gp_flag(): 
 ###Update grab_past_flag#####
    dictObj = []

    # Check if file exists
    if path.isfile(SECRET_DATABASE) is False:
        raise Exception("File not found")
    
    # Read JSON file
    with open(SECRET_DATABASE) as fp:
        dictObj = json.load(fp)
    
        # "grab_past_flag" : 0
        dictObj.update({"grab_past_flag": 1})
    
        with open(SECRET_DATABASE, 'w') as json_file:
            json.dump(dictObj, json_file, 
                        indent=4,  
                        separators=(',',': '))
    
        print(pgrm_signature + 'Successfully updated setup.json')
 
# Get the message sender data
def getSender(msg):
    # get the sender id
    senderId = msg.author.id

    # return the sender ID to be used in dupCheck to be recorded in the songs playlist
    return senderId

# returns the formatted time stamp
def getTimestamp(msg):
    # Get the timestamp from the message
    timestamp = msg.created_at

    # Format the timestamp as a string
    formatted_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # return the sender ID to be used in dupCheck to be recorded in the songs playlist
    return formatted_timestamp

# Returns the message ID of a msg
def getMessageID(msg):
    # Get the ID for the message on discord
    message_id = str(msg.id)

    # return the sender ID to be used in dupCheck to be recorded in the songs playlist
    return message_id

# Initialize the database if not created yet
database_tools.initialize_milestones('databases/spotbot.db', PLAYLIST_CHANNEL)

bot.run(TOKEN)

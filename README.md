# Spotbot 2
A discord bot that scrapes users spotify links from a set channel and automatically adds those songs to a set spotify playlist. Think of it like an *over* engineered collaborative playlist.


## Table of Contents
- [Requirements](#requirements)
- [Install](#install)
- [Contributing](#contributing)
- [License](#license)


## Requirements
[![Python 3.10.9](https://img.shields.io/badge/Python-3.10.9-306a98?logo=Python&logoColor=fcdf5a)](https://www.python.org/) 


## Install
1. Go to https://developer.spotify.com/dashboard/ refimage1 in image_refrences.pdf 
    
    a. Press Login

    b. Create App (refimage2)
    
    c. Copy and paste the corrosponging client id and client secret in their respective places in setup.json (refimage3)
    
    d. select Edit Settings and fillout fields detailed in (refimage4)
    
 2. Go to https://discord.com/developers/
    
    a. Create a new application (refimage5)
    
    b. Go to the bot tab > select create bot 
    
    c. Press reset access token (refimage6) and paste that token in "discord_token" : "place token here" in setup.json
    
    d. Copy and past access token into setup.json
    
    e. Turn on switches just like refimage7
    
    f. In the sidebar, you'll find the OAuth2 go to general and place http://localhost:5000/callback in redirecturi (refimage8)
    
    g. In the sidebar, go to URL Genreator. Fill out feilds just like refimage 9 & 10 **NOTE you only need *bot* & *messages.read* to use this type of bot when looking at refimage9** 
    
    h. Invite the bot to the server you want it to run in
    
    i. Grab the link to the chat you want the bot to run in; right click on a discord channel and select copyID (refimage11)
    
    j. Paste the ID you recieved in the "discord_channel" : "place the discord channel you want the bot to read here" inside of the setup.json file

3. Get spotify playlist link that the bot will add to
    
    a. Add that link into setup.json in the correct field ex:"https://open.spotify.com/playlist/0XM....8226c884a3d" (needs to be a playlist you made on your own personal spotify account)
    
4. All fields in `setup.json` should be filled out and look like refimage12. A template `setup.json` can be extracted from [`setup.zip`](https://github.com/wildxmxtt/spotbot2/blob/main/database.py).

5. Install requrements.txt to your machine 
    
    ```cmd 
    pip install -r requirements.txt
    ```
    
6. Run app.py (only needs to be done once)
    
    a. In your terminal type:
    ```cmd
    flask run
    ```
    or host externally with:
    ```cmd
    flask run --host=0.0.0.0 --port=5000
    ```

    b. Go to https://localhost:5000 (or address of host)
    
    c. Login with your spotify username and password
    
    d. Once logged in on the webpage you should get the number of songs in the playlist you placed in setup.json refimage(13 & 15)
    
    e. Ctrl + c in terminal (app.py will never need to be ran again, as it is only used to **generate** a token for your bot to use)
    
 7. Run spotbot.py
    ```cmd
    python3 spotbot.py
    ```

    (If you dont have past songs you want to grab skip steps b and c and set the grabpast flag to 1 in setup.json or else it will break the code)
    
    a. Once in the terminal it should read "spotbot.py: SpotifyBot: ON" (refimage16)
    
    b. Type `!grabPast` in the channel you specified in step 2j; This will grab all past spotify links sent in the chat **If you want to run this command and you have more than 500000 messages in your chat go to *line 62* in spotbot.py and increase the number as much as needed** 
    
    c. Once `!grabPast` is ran you should see it act like refrence (image18), grabpast can only be ran once, if this needs to be changed go to the setup.json file and set the flag back to 0 instead of 1

8. Now when songs are sent to the channel it will automatically send them to spotify! (refimage 20 & 21)


## Contributing
If something is wrong, [Open an issue.](http://github.com/wildxmxtt/spotbot2/issues/new)

This project exists thanks to all the people who contribute.

<a href="https://github.com/wildxmxtt/spotbot2/graphs/contributors"><img src="https://contrib.rocks/image?repo=wildxmxtt/spotbot2" /></a>


## License
[MIT](LICENSE) © Matthew Wilde
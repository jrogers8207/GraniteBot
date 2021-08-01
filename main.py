# Granitebot: A general purpose bot for Discord.
# Copyright (C) 2021 Jack Rogers

import datetime
import logging
from pathlib import Path
import sys

import discord
from discord.ext import tasks
import nest_asyncio
import rtoml
import twint
from twint.token import RefreshTokenException
import twitch

# Perform startup tasks.
logging.basicConfig(
    level=logging.DEBUG, format=" %(asctime)s - %(levelname)s - %(message)s"
)
logging.disable(logging.DEBUG)
nest_asyncio.apply()
# Create and setup configuration file if it doesn't exist
configurationFilePath = Path("config.toml")
if not configurationFilePath.is_file():
    logging.info("config.toml doesn't exist. Generating default config.toml")
    configurationFile = open(configurationFilePath, "w")
    configurationFile.write(
        r"""[discord]
token = ""
status = ""


[twitch]
enabled = false
username = ""
clientID = ""
clientSecret = ""
updateFrequency = 60
discordPostChannelID = 


[twitter]
enabled = false
username = ""  # Twitter handle WITHOUT @ symbol.
updateFrequency = 60  # Time in seconds
discordPostChannelID = """
    )
    print(
        "First time setup complete. Please edit config.toml to your preferences and restart the program."
    )
    configurationFile.close()
    logging.info("Configuration file successfully created. Now exiting...")
    sys.exit(0)

logging.info("STARTUP: config.toml exists. Continuing...")
logging.info("STARTUP: Parsing config.toml...")
configuration = rtoml.load(configurationFilePath)

if configuration["twitch"]["enabled"]:
    client = twitch.TwitchHelix(
        client_id=configuration["twitch"]["clientID"],
        client_secret=configuration["twitch"]["clientSecret"],
        scopes=["analytics:read:extensions"],
    )


class GraniteClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if configuration["twitter"]["enabled"]:
            self.updateTwitterPosts.start()
        if configuration["twitch"]["enabled"]:
            self.twitchLiveAlert.start()

    async def onReady(self):
        logging.info("Logged in as {self.user} (ID: {self.user.id})")

    @tasks.loop(seconds=configuration["twitter"]["updateFrequency"])
    async def updateTwitterPosts(self) -> None:
        # Configure the search.
        twintConfiguration = twint.Config()
        twintConfiguration.Username = configuration["twitter"]["username"]
        twintConfiguration.Since = (
            datetime.datetime.now()
            - datetime.timedelta(seconds=configuration["twitter"]["updateFrequency"])
        ).strftime("%Y-%m-%d %H:%M:%S")
        newTweets = []
        twintConfiguration.Store_object = True
        twintConfiguration.Store_object_tweets_list = newTweets
        # Run the search.
        logging.info(f"TWITTER: Scraping tweets since {twintConfiguration.Since}.")
        try:
            twint.run.Search(twintConfiguration)
        except RefreshTokenException:
            logging.error("A token refresh exception occurred.")

        # Post tweet to Discord.
        if newTweets:
            logging.info("TWITTER: Posting tweet(s) to Discord.")
            for tweet in newTweets:
                await self.get_channel(
                    configuration["twitter"]["discordPostChannelID"]
                ).send(tweet.link)
        logging.info(
            f"TWITTER: Sleeping for {configuration['twitter']['updateFrequency']} seconds."
        )

    @updateTwitterPosts.before_loop
    async def waitForLoginTwitter(self):
        await self.wait_until_ready()  # wait until logged in

    currentlyLive = False

    @tasks.loop(seconds=configuration["twitch"]["updateFrequency"])
    async def twitchLiveAlert(self):
        # Check if Twitch stream is newly live.
        logging.info("TWITCH: Checking if Twitch stream recently went live.")
        client.get_oauth()
        stream = client.get_streams(user_logins=configuration["twitch"]["username"])
        if stream and self.currentlyLive == False:
            # Post alert message to Discord.
            logging.info("DISCORD: Posting alert(s) to Discord.")
            await self.get_channel(
                configuration["twitch"]["discordPostChannelID"]
            ).send(
                "@everyone "
                + configuration["twitch"]["username"]
                + " is now live on Twitch! https://twitch.tv/"
                + configuration["twitch"]["username"]
            )
            self.currentlyLive = True
        elif not stream:
            self.currentlyLive = False

        logging.info("TWITCH: Sleeping for 60 seconds.")

    @twitchLiveAlert.before_loop
    async def waitForLoginTwitch(self):
        await self.wait_until_ready()


# Set Discord status.
if configuration["discord"]["status"].startswith("Playing"):
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name=configuration["discord"]["status"].replace("Playing", "", 1),
    )
elif configuration["discord"]["status"].startswith("Watching"):
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name=configuration["discord"]["status"].replace("Watching", "", 1),
    )
elif configuration["discord"]["status"].startswith("Listening"):
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name=configuration["discord"]["status"].replace("Listening", "", 1),
    )
elif configuration["discord"]["status"].startswith("Competing"):
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name=configuration["discord"]["status"].replace("Competing", "", 1),
    )
else:
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name=configuration["discord"]["status"].replace("Competing", "", 1),
    )


logging.info("STARTUP: Starting up client...")
discordClient = GraniteClient(activity=activity)
discordClient.run(configuration["discord"]["token"])

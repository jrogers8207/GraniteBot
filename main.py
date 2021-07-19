import datetime
import logging
from pathlib import Path
import sys
import threading
import time

import rtoml
import twint

# Perform startup tasks.
logging.basicConfig(level=logging.DEBUG, format=" %(asctime)s - %(levelname)s - %(message)s")

# Create and setup configuration file if it doesn't exist
configurationFilePath = Path("config.toml")
if not configurationFilePath.is_file():
    logging.info("config.toml doesn't exist. Generating default config.toml")
    configurationFile = open(configurationFilePath, "w")
    configurationFile.write(
        "[twitter]\nusername = \"\" # Handle WITHOUT @  symbol goes in quotes.\nupdateFrequency = 60 # Time in seconds")
    print("First time setup complete. Please edit config.toml to your preferences and restart the program.")
    configurationFile.close()
    logging.info("Configuration file successfully created. Now exiting...")
    sys.exit(0)

logging.info("STARTUP: config.toml exists. Continuing...")
logging.info("STARTUP: Parsing config.toml...")
configuration = rtoml.load(configurationFilePath)


def updateTwitterPosts() -> None:
    while True:
        # Configure the search.
        twitterUpdateFrequency = configuration["twitter"]["updateFrequency"]
        twintConfiguration = twint.Config()
        twintConfiguration.Username = configuration["twitter"]["username"]
        twintConfiguration.Since = (datetime.datetime.now() - datetime.timedelta(seconds=twitterUpdateFrequency)).strftime("%Y-%m-%d %H:%M:%S")

        # Run the search.
        logging.info(f"TWITTER: Scraping tweets since {twintConfiguration.Since}.")
        twint.run.Search(twintConfiguration)
        # Post tweet to Discord.
        logging.info("TWITTER: Posting tweet to Discord. Not yet implemented.")
        logging.info(f"TWITTER: Sleeping for {twitterUpdateFrequency} seconds.")
        time.sleep(twitterUpdateFrequency)

logging.info("Creating and starting Twitter thread.")
twitterThread = threading.Thread(target=updateTwitterPosts)
twitterThread.start()

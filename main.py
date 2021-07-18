import datetime
import logging
from pathlib import Path
import sys
import time

import rtoml
import twint

# Perform startup tasks.
logging.basicConfig(filename="log.txt", level=logging.DEBUG, format=" %(asctime)s - %(levelname)s - %(message)s")

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

import os
import json
import time
import datetime

from spotifyclient import SpotifyClient
from helpers import *


def main():
    spotify_client = SpotifyClient(os.getenv("SPOTIFY_AUTHORIZATION_TOKEN"),
                                   os.getenv("SPOTIFY_USER_ID"))
    test = spotify_client.get_playing_with_context()
    spotify_client.skip(+3)


if __name__ == "__main__":
    main()

import json
import os
import re
import time

import requests

from track import Track
from playlist import Playlist


class SpotifyClient:
    """SpotifyClient performs operations using the Spotify API."""
    market = "DE"

    def __init__(self, authorization_token, user_id, market_="DE"):
        """
        :param authorization_token: Spotify API token
        :param user_id: Spotify user id
        :param market_: Synonym for country. An ISO 3166-1 alpha-2 country code or the string from_token.
        Supply this parameter to limit the response to one particular geographical market.
        For example, for albums available in Sweden: market=SE.
        """
        self._authorization_token = authorization_token
        # self._authorization_token = "------"
        self._user_id = user_id
        self.market = market_

    def _place_get_api_request(self, url):
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._authorization_token}"
            }
        )
        return response

    def _place_post_api_request(self, url, data=None):
        if not data:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._authorization_token}"
                }
            )
        else:
            response = requests.post(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._authorization_token}"
                }
            )

        return response

    def get_playing(self, market=market):
        """
        Get the currently playing song by a user
        :param market: Synonym for country. An ISO 3166-1 alpha-2 country code or the string from_token.
        Supply this parameter to limit the response to one particular geographical market.
        For example, for albums available in Sweden: market=SE.
        It can also be globally set for the whole SpotifyClient object.
        """
        url = f"https://api.spotify.com/v1/me/player/currently-playing?market={market}&additional_types=track,episode"
        response = self._place_get_api_request(url)
        if response.status_code >= 400:
            # something bad happened
            print(response)
            raise Exception(response)
        if response.status_code == 204:
            # nothing to report, but everything fine
            print("nothing playing")
            return
        if response.status_code == 200:
            return response.json()

        print("Wut?\n")
        print("response")
        return

    def get_album_songs(self, album_uri, market=market, limit=50):
        """
        Get the content of an album and strip everything but the Spotify URI
        :param album_uri: URI or ID of the album (with or without 'spotify:album:')
        :param market: Synonym for country. An ISO 3166-1 alpha-2 country code or the string from_token.
        Supply this parameter to limit the response to one particular geographical market.
        For example, for albums available in Sweden: market=SE.
        It can also be globally set for the whole SpotifyClient object.
        :param limit: The maximum number of tracks to return. Default: 50. Minimum: 1. Maximum: 50
        """
        # album_uri = album_uri.removeprefix('spotify:album:')
        # pattern = r"^spotify:album:"
        pattern = r"(spotify:album:|spotify:.*:album:)(?=[0-9A-Za-z_-]{22}$)"
        album_uri = re.sub(pattern, "", album_uri)
        songs = []
        next = f"https://api.spotify.com/v1/albums/{album_uri}/tracks?market={market}&limit={limit}"
        while next:
            response = self._place_get_api_request(next)
            response = response.json()

            for song in response['items']:
                songs.append(song['uri'])

            next = response['next']
            # album with 100 songs 0evSqptUFUbxZjrtgSwZAq
        return songs

    def get_playlist_songs(self, playlist_uri, market=market, limit=100):
        """
        Get the content of an album and strip everything but the Spotify URI
        :param playlist_uri: URI or ID of the album (with or without 'spotify:album:')
        :param market: Synonym for country. An ISO 3166-1 alpha-2 country code or the string from_token.
        Supply this parameter to limit the response to one particular geographical market.
        For example, for albums available in Sweden: market=SE.
        It can also be globally set for the whole SpotifyClient object.
        :param limit: The maximum number of tracks to return. Default: 100. Minimum: 1. Maximum: 100
        """
        # album_uri = album_uri.removeprefix('spotify:playlist:')
        pattern = r"^(spotify:playlist:|spotify:.*:playlist:)(?=[0-9A-Za-z_-]{22}$)"
        playlist_uri = re.sub(pattern, "", playlist_uri)
        songs = []
        next = f"https://api.spotify.com/v1/playlists/{playlist_uri}/tracks?market={market}&fields=items(track(uri)),next&limit={limit}&additional_types=track,episode"
        while next:
            response = self._place_get_api_request(next)
            response = response.json()

            for song in response['items']:
                songs.append(song['track']['uri'])

            next = response['next']

        return songs

    def get_track_recommendations(self, seed_tracks, limit=50):
        """Get a list of recommended tracks starting from a number of seed tracks.

        :param seed_tracks: (list of Track) Reference tracks to get recommendations. Should be 5 or less.
        :param limit: Number of recommended tracks to be returned
        :return tracks (list of Track): List of recommended tracks
        """
        seed_tracks_url = ""
        for seed_track in seed_tracks:
            seed_tracks_url += seed_track.id + ","
        seed_tracks_url = seed_tracks_url[:-1]
        url = f"https://api.spotify.com/v1/recommendations?seed_tracks={seed_tracks_url}&limit={limit}"
        response = self._place_get_api_request(url)
        response_json = response.json()
        tracks = [Track(track["name"], track["id"], track["artists"][0]["name"]) for
                  track in response_json["tracks"]]
        return tracks

    def create_playlist(self, name):
        """
        :param name: New playlist name
        :return playlist: Newly created playlist
        """
        data = json.dumps({
            "name": name,
            "description": "Recommended songs",
            "public": True
        })
        url = f"https://api.spotify.com/v1/users/{self._user_id}/playlists"
        response = self._place_post_api_request(url, data)
        response_json = response.json()

        # create playlist
        playlist_id = response_json["id"]
        playlist = Playlist(name, playlist_id)
        return playlist

    def populate_playlist(self, playlist, tracks):
        """Add tracks to a playlist.

        :param playlist: Playlist to which to add tracks
        :param tracks: (list of Track) Tracks to be added to playlist
        :return response: API response
        """
        track_uris = [track.create_spotify_uri() for track in tracks]
        data = json.dumps(track_uris)
        url = f"https://api.spotify.com/v1/playlists/{playlist.id}/tracks"
        response = self._place_post_api_request(url, data)
        response_json = response.json()
        return response_json

    def get_playing_with_context(self, market=market):
        """
        Get the currently playing track with all possible reference to return to the current player state.
        :param market: Synonym for country. An ISO 3166-1 alpha-2 country code or the string from_token.
        Supply this parameter to limit the response to one particular geographical market.
        For example, for albums available in Sweden: market=SE.
        It can also be globally set for the whole SpotifyClient object.
        """

        test = None

        i = 10
        while test is None and i > 0:
            i -= 1
            time.sleep(0.5)
            test = self.get_playing(market)
            # print(test)
        if test is None:
            return

        output = {'item': {'uri': test['item']['uri'], 'duration_ms': test['item']['duration_ms']},
                  'progress_ms': test['progress_ms'], 'is_playing': test['is_playing']}

        if test['context'] is not None:

            output.update({'context': {'type': test['context']['type'], 'uri': test['context']['uri']}})

            if test['context']['type'] == 'album':
                output.update({'context': {'offset': self.get_album_songs(test['context']['uri'], market).index(test['item']['uri'])}})
            elif test['context']['type'] == 'playlist':
                output.update({'context': {'offset': self.get_playlist_songs(test['context']['uri'], market).index(test['item']['uri'])}})

        else:
            output['context'] = None

        return output

    def skip(self, tracks: int):
        if tracks is 0:
            return

        data = None
        check = self.get_playing()
        if check is None:
            return
        check = check['item']['uri']

        if tracks > 0:  # skip to next

            url = f"https://api.spotify.com/v1/me/player/next"
            while tracks != 0:
                if self._place_post_api_request(url, data).status_code != 204:
                    # something bad happened
                    raise Exception()
                check_ = check
                check = self.get_playing("DE")['item']['uri']
                if check_ is not check:
                    tracks -= 1

        elif tracks < 0:  # skip to previous

            url = f"https://api.spotify.com/v1/me/player/previous"
            while tracks != 0:
                if self._place_post_api_request(url, data).status_code != 204:
                    # something bad happened
                    raise Exception()
                check_ = check
                check = self.get_playing("DE")['item']['uri']
                if check_ is not check:
                    tracks += 1

import collections

import requests
import json

import random
import string

import re 

# items = ['albums', 'artists', 'audioepisodes', 'genres', 'playlists', 'profiles', 'shows', 'topHit', 'topRecommendations', 'tracks']

class SpotifyUser:

	def __init__(self, auth_cookie):

		self.headers = {
							'accept': "application/json",
							'accept-encoding': "gzip, deflate, br",
							'accept-language': "nl",
							'app-platform': "WebPlayer",
							'origin': 'https://open.spotify.com',
							'referer': 'https://open.spotify.com/',
							'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
							'sec-ch-ua-mobile': '?0',
							'sec-fetch-dest': 'empty',
							'sec-fetch-mode': 'cors',
							'sec-fetch-site': 'same-site',
							'spotify-app-version': "1.1.61.345.g642a5b0d",
							'user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
						}

		# Calling functions to initialize some class vars

		self.get_token(auth_cookie)
		self.username = self.get_user_info()['id']

	def get_token(self, cookie):

		url = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
		this_req_headers = {"cookie": f"sp_dc={cookie};"}

		resp = requests.get(url, headers=this_req_headers)

		self.headers.update({'authorization': f"Bearer {resp.json()['accessToken']}"})

	def get_track_by_id(self, id):

		url = f"https://api.spotify.com/v1/tracks/{id}"
		resp = requests.get(url, headers=self.headers)

		return (resp.json())

	def get_artist_by_id(self, id):

		url = f"https://api.spotify.com/v1/artists/{id}"
		resp = requests.get(url, headers=self.headers)

		return (resp.json())

	def get_id_from_item(self, item, name):

		url = f"https://spclient.wg.spotify.com/searchview/km/v4/search/{name}?entityVersion=2&limit=10&imageSize=large&catalogue=&country=NL&username={self.username}&locale=nl&platform=web"
		resp = requests.get(url, headers=self.headers).json()

		return resp['results'][item]['hits'][0]['uri'].split(':')[2]

	def get_playlist(self, playlist):

		songs = []

		url = f"https://api.spotify.com/v1/playlists/{playlist}/tracks?offset=0&limit=100&additional_types=track%2Cepisode&market=from_token"
		resp = requests.get(url, headers=self.headers).json()
		
		songs.extend(resp['items'])
		while resp['next'] != None:

			url = resp['next']
			resp = requests.get(url, headers=self.headers).json()
			songs.extend(resp['items'])

		return songs

	def get_liked_songs(self, offset=0):

		songs = []

		url = "https://api.spotify.com/v1/me/tracks?limit=50&offset=0&market=from_token"
		resp = requests.get(url, headers=self.headers).json()

		songs.extend(resp['items'])
		while resp['next'] != None:

			url = resp['next']
			resp = requests.get(url, headers=self.headers).json()
			songs.extend(resp['items'])

		return songs

	def create_playlist(self, name):

		url = "https://spclient.wg.spotify.com/playlist/v2/playlist"

		headers = {	'content-length': "99",
					'content-type': "application/json;charset=UTF-8"}
		headers.update(self.headers)
		payload = json.dumps({"ops":[{"kind":6,"updateListAttributes":{"newAttributes":{"values":{"name":name}}}}]})

		resp = requests.post(url, headers=headers, data=payload).json()

		return resp

	def confirm_playlist(self, uri):

		url = f"https://spclient.wg.spotify.com/playlist/v2/user/{self.username}/rootlist/changes"

		headers = {	'content-length': "99",
					'content-type': "application/json;charset=UTF-8"}
		headers.update(self.headers)

		revision = self.get_revision()
		payload = json.dumps({"baseRevision": revision,"deltas":[{"ops":[{"kind":"ADD","add":{"fromIndex":0,"items":[{"uri":uri,"attributes":{"addedBy":"","timestamp":"1622145865369","seenAt":"0","public":False,"formatAttributes":[]}}],"addLast":False,"addFirst":True}}],"info":{"user":"","timestamp":"0","admin":False,"undo":False,"redo":False,"merge":False,"compressed":False,"migration":False,"splitId":0,"source":{"client":"WEBPLAYER","app":"","source":"","version":""}}}],"wantResultingRevisions":False,"wantSyncResult":False,"nonces":[]})

		resp = requests.post(url, headers=headers, data=payload).json()
		return resp

	def post_song(self, playlist_id, song_uri):

		url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
		payload = json.dumps({"uris":[song_uri],"position":None})

		resp = requests.post(url, headers=self.headers, data=payload)
		return resp

	def get_user_info(self):

		url = "https://api.spotify.com/v1/me"
		resp = requests.get(url, headers=self.headers).json()

		return resp

	def get_playlists_for_me(self):	

		url = f"https://spclient.wg.spotify.com/playlist/v2/user/{self.username}/rootlist?"
		params = {  'decorate': 'revision,length,attributes,timestamp,owner',
					'revision': ''}
		resp = requests.get(url, params=params, headers=self.headers).json()
		playlists = resp['contents']

		return playlists

	def get_revision(self):

		url = f"https://spclient.wg.spotify.com/playlist/v2/user/{self.username}/rootlist?"
		params = {  'decorate': 'revision,length,attributes,timestamp,owner',
					'revision': ''}

		resp = requests.get(url, params=params, headers=self.headers).json()
		
		return resp['revision']

	def get_single_track(self):

		url = "https://api.spotify.com/v1/tracks/3JWiDGQX2eTlFvKj3Yssj3"

		resp = requests.get(url, headers=self.headers).json()

		return resp

class SpotifyTinkerer(SpotifyUser):

	def __init__(self, auth_cookie):

		super().__init__(auth_cookie)

	def create_playlist(self, name):

		my_playlists = super().get_playlists_for_me()

		for idx, play in enumerate(my_playlists['metaItems']):

			if name == play['attributes']['name']:

				playlist_uri = my_playlists['items'][idx]['uri']
				playlist_id = playlist_uri.split(":")[2]

				pl = {"name":name, "id":playlist_id, "uri":playlist_uri}
				return pl

		playlist_response_json = super().create_playlist(name)
		

		playlist_uri = playlist_response_json['uri']
		playlist_revision = playlist_response_json['revision']

		playlist_id = playlist_uri.split(":")[2]

		temp_confirmed = super().confirm_playlist(playlist_uri)

		pl = {"name":name, "id":playlist_id, "uri":playlist_uri}

		return pl

	def divide_into_genres(self, popularity_threshold, playlist="liked"):

		songs_divided = {}

		if playlist=="liked":
			mysongs = super().get_liked_songs()

		else:
			
			use_playlist = re.findall(r"[0-9].{21}", playlist)[0]
			mysongs = super().get_playlist(use_playlist)

		for i_song in mysongs:

			song = i_song['track']

			if song == None:
				continue
				
			if popularity_threshold < song['popularity']:

				artist = song['artists'][0]

				genres = super().get_artist_by_id(artist['id'])['genres'] # TEMP
				artist_about = {'name': artist['name'], 'id':artist['id'], 'uri':artist['uri'], 'genres':genres} # TEMP

				song_about = {'name': song['name'], 'popularity': song['popularity'], 'id':song['id'], 'uri':song['uri'],'artist':artist_about} # Only important dictionary

				genres = song_about['artist']['genres'] # Reusing genres var

				for key in songs_divided:

					for genre in genres:
						if genre == key:
							songs_divided[key].append(song_about)
							genres.remove(genre)

				for genre in genres:

					songs_divided[genre] = [song_about]

		return songs_divided

	def push_songs_in_playlist(self, playlist, song_dict, acceptable_genres = "all"):

		temp_songs = super().get_playlist(playlist['id'])
		used_songs = [ x['track']['uri'] for x in temp_songs]

		for genre in song_dict.keys():

			use_these_songs = False

			if acceptable_genres == "all":
				use_these_songs = True

			else:
				for ac in acceptable_genres:
					if ac in genre:
						use_these_songs = True

			if use_these_songs:

				for song in song_dict[genre]:
					if song['uri'] not in used_songs:
						super().post_song(playlist['id'],song['uri'])
						used_songs.append(song['uri'])
	
if __name__ == '__main__':

	
	with open("config.json", "r") as f:

		config = json.load(f)

	if config["sp_dc_auth_cookie"] == "":
		exit()

	spotf = SpotifyTinkerer(config["sp_dc_auth_cookie"])


	songs_from_playlist = spotf.divide_into_genres(config["popularity_threshold"], config["playlist_link_scrape"]) # Link to a playlist or liked( for liked songs )
	
	with open('genres_chosen_playlist.json', 'w') as f:

		json.dump(songs_from_playlist, f, indent=4)

	if config["playlist_name_push"] != None:
		
		created_pl = spotf.create_playlist(config["playlist_name_push"])
		spotf.push_songs_in_playlist(created_pl, songs_from_playlist, config["genres"])

	print("DONE!")
	

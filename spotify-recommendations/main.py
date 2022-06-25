import spotipy
from spotipy.oauth2 import SpotifyOAuth
from sklearn.cluster import KMeans
import acct1_credentials
import acct2_credentials
import pandas as pd
import re

def get_all_saved_tracks(user, limit_step=1):
    name, popularity, release_date, track_uri, artist_name, artist_uri = [], [], [], [], [], []
    for offset in range(0, 10000000, limit_step):
        response = user.current_user_saved_tracks(
            limit=limit_step,
            offset=offset,
        )
        if response['items'] == []:
            break
        name.append(response['items'][0]['track']['name'])
        popularity.append(response['items'][0]['track']['popularity'])
        release_date.append(response['items'][0]['track']['album']['release_date'])
        track_uri.append(response['items'][0]['track']['uri'])
        artist_name.append(response['items'][0]['track']['artists'][0]['name']) 
        artist_uri.append(response['items'][0]['track']['artists'][0]['uri']) 

    
    d = {"name": name, "popularity": popularity, "release_date": release_date, "track_uri": track_uri, "artist_name": artist_name, "artist_uri": artist_uri}
    df = pd.DataFrame(d)

    return df

def get_genres(artist_uri, sp):
    artist_uri = re.search(r'(?<=spotify:artist:)[^.\s]*',artist_uri).group()
    artist = sp.artist(artist_uri)

    return artist['genres']

def get_genre_counts(df):
    liked_genres_df = pd.melt(df.genres.apply(pd.Series).reset_index(), 
        id_vars=['index'],
        value_name='genres') \
        .drop('variable', axis=1) \
        .sort_values('index') \
        .dropna()

    liked_genres_df = liked_genres_df.groupby(['genres'])['genres'].count()
    return liked_genres_df

def get_playlist_tracks(user, playlist_id):
    tracks = []
    playlist = user.playlist(playlist_id, fields=None, market=None, additional_types=('track', ))
    
    for track in playlist['tracks']['items']:
        tracks.append(track['track'])
    
    return tracks

def get_playlists(user, limit_step=1, regex="^.*$"):   
    name, track, genres = [], [], []
    for offset in range(0, 10000000, limit_step):
        response = user.current_user_playlists(
            limit=limit_step,
            offset=offset,
        )
        if response['items'] == []:
            break  
        if re.search(regex, response['items'][0]['name']):
        #if response['items'][0]['name'].startswith('DW'):
            tracks = get_playlist_tracks(sp, response['items'][0]['id'])

            for song in tracks:
                name.append(response['items'][0]['name'])
                track.append(song['name'])
                genres.append(get_genres(song['artists'][0]['uri'], user))
        
    d = {"name": name, "track": track, "genres": genres}
    df = pd.DataFrame(d)

    return df

def get_match(genres, supergenres, which):
    is_match = False
    supergenre = None
    
    for genre in genres:
        for key,value in supergenres.items():
            if genre in value:
                is_match = True
                supergenre = key
    
    return supergenre if which == 'supergenre' else is_match

def add_match_and_supergenre(df, supergenres):
    df['is_match'] = df['genres'].apply(get_match, supergenres = supergenres, which = 'is_match')
    df['supergenre'] = df['genres'].apply(get_match, supergenres = supergenres, which = 'supergenre')
    
    return df

def get_match_percentage(df, supergenres):
    df['is_match'] = df['genres'].apply(get_match, supergenres = supergenres, which = 'is_match')
    df['supergenre'] = df['genres'].apply(get_match, supergenres = supergenres, which = 'supergenre')
    
    df = df[df['genres'].str.len() != 0] 
    
    true_vals = df[df['is_match']].groupby(['name']).size().reset_index(name='true') 
    false_vals = df[df['is_match'] == False].groupby(['name']).size().reset_index(name='false') 
    
    df = pd.merge(true_vals, false_vals)
    df['% match'] = df['true'] / (df['true'] + df['false'])
    
    return df

def get_followed_artists(user):   
    name, genres = [], []
    response = user.current_user_followed_artists(limit=50)
    
    if response['artists']['items'] != []:
        
        for artist in response['artists']['items']:
            name.append(artist['name'])
            genres.append(artist['genres'])
        
    d = {"name": name, "genres": genres}
    df = pd.DataFrame(d)

    return df

def get_saved_albums(user, limit_step=1):   
    name, genres = [], []
    for offset in range(0, 10000000, limit_step):
        response = user.current_user_playlists(
            limit=limit_step,
            offset=offset,
        )
    
    if response['items'] != []:
        
        for album in response['items']:
            name.append(album['album']['name'])
            genres.append(get_genres(album['album']['tracks']['items'][0]['artists'][0]['uri'], user))
                
    d = {"name": name, "genres": genres}
    df = pd.DataFrame(d)

    return df


def main():

    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct2_credentials.client_ID, client_secret= acct2_credentials.client_SECRET, redirect_uri=acct2_credentials.redirect_url, scope=scope))
    print("success!")
    #liked_tracks_df = get_all_saved_tracks(sp)

    urban       = ['alternative hip hop', 'hip hop', 'rap', 'underground hip hop', 'experimental hip hop', 'abstract hip hop', 'conscious hip hop', 'east coast hip hop', 'boom bap', 'psychedelic hip hop', 'trip hop', 'urbano espanol']
    art_chamber = ['art pop', 'chamber pop']
    metropolis  = ['escape room', 'pop', 'dance pop', 'electropop', 'uk pop', 'metropopolis', 'dream pop', 'hyperpop', 'experimental pop', 'proto-hyperpop', 'indietronica']
    electronic  = ['electronica', 'uk bass', 'deconstructed club', 'wonky', 'witch house', 'microhouse', 'intelligent dance music', 'fluxwork', 'grave wave', 'hauntology', 'classic dubstep', 'jungle', 'glitchbreak', 'atmospheric dnb', 'wave', 'future garage', 'new rave', 'ambient', 'alternative dance', 'uk experimental electronic', 'big beat']
    alt_rock    = ['indie rock', 'alternative rock', 'rock', 'post-rock', 'experimental rock']
    caribbean   = ['dancehall', 'reggae fusion', 'traphall', 'jamaican hip hop']
    emo         = ['emo', 'dreamo', 'alternative emo', 'midwest emo']

    supergenres = {
        'urban' : urban,
        'art_chamber' : art_chamber,
        'metropolis' : metropolis,
        'electronic' : electronic,
        'alt_rock' : alt_rock,
        'caribbean' : caribbean,
        'emo' : emo
    }   

    #liked_tracks_df['genres'] = liked_tracks_df['artist_uri'].apply(get_genres, sp = sp)

    #liked_artists_df = liked_tracks_df.groupby(['artist_name'])['artist_name'].count()

    #liked_genres_df = get_genre_counts(liked_tracks_df).sort_values(ascending = False)



if __name__=="__main__":
    main()
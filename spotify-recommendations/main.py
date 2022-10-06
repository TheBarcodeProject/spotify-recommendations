from cmath import nan
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from sklearn.cluster import KMeans
import acct1_credentials
import acct2_credentials
import pandas as pd
import re
from collections import Counter
from ast import literal_eval
import numpy as np
import os

def get_all_saved_tracks(user, limit_step=1):
    """ Returns dataframe with all the user's saved tracks """
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
    """ Recieves an artist_uri and returns the genres associated to the artist """
    artist_uri = re.search(r'(?<=spotify:artist:)[^.\s]*',artist_uri).group()
    artist = sp.artist(artist_uri)

    return artist['genres']

def get_playlist_tracks(user, playlist_id):
    """ Get tracks from a playlist """
    tracks = []
    playlist = user.playlist(playlist_id, fields=None, market=None, additional_types=('track', ))
    
    for track in playlist['tracks']['items']:
        tracks.append(track['track'])
    
    return tracks

def get_playlists(user, limit_step=1, regex="^.*$"): 
    """ Get user's saved playlists """  
    name, track, genres = [], [], []
    for offset in range(0, 10000000, limit_step):
        response = user.current_user_playlists(
            limit=limit_step,
            offset=offset,
        )
        if response['items'] == []:
            break  
        if re.search(regex, response['items'][0]['name']):
            tracks = get_playlist_tracks(user, response['items'][0]['id'])

            for song in tracks:
                name.append(response['items'][0]['name'])
                track.append(song['name'])
                genres.append(get_genres(song['artists'][0]['uri'], user))
        
    d = {"name": name, "track": track, "genres": genres}
    df = pd.DataFrame(d)

    return df

def get_match(genres, supergenres, which):
    """ Returns true if the genre falls within a supergenre, false otherwise """
    is_match = False
    supergenre = None
    
    for genre in genres:
        for key,value in supergenres.items():
            if genre in value:
                is_match = True
                supergenre = key
    
    return supergenre if which == 'supergenre' else is_match

def add_match_and_supergenre(df, supergenres):
    """ Adds match value and supergenre to dataframe """
    df['is_match'] = df['genres'].apply(get_match, supergenres = supergenres, which = 'is_match')
    df['supergenre'] = df['genres'].apply(get_match, supergenres = supergenres, which = 'supergenre')
    
    return df

def get_match_percentage(df):
    """ Calculates the percentage of tracks in dataframe which match a supergenre """
    df = df[df['genres'].str.len() != 0] 
    
    true_vals = df[df['is_match']].groupby(['name']).size().reset_index(name='true') 
    false_vals = df[df['is_match'] == False].groupby(['name']).size().reset_index(name='false') 
    
    df = pd.merge(true_vals, false_vals)
    df['% match'] = df['true'] / (df['true'] + df['false'])
    
    return df

def get_followed_artists(user):   
    """ Returns user's followed artists """
    name, genres = [], []
    response = user.current_user_followed_artists(limit=50)
    
    if response['artists']['items'] != []:
        
        for artist in response['artists']['items']:
            name.append(artist['name'])
            genres.append(artist['genres'])
        
    d = {"name": name, "genres": genres}
    df = pd.DataFrame(d)

    return df

def get_saved_albums(user):   
    """ Returns user's saved albums """
    dfs = []
    offset = 0
    
    for i in range(3):
        name, genres = [], []
        response = user.current_user_saved_albums(limit=50, offset=offset)
        if response['items'] != []:
            for album in response['items']:
                name.append(album['album']['name'])
                genres.append(get_genres(album['album']['tracks']['items'][0]['artists'][0]['uri'], user))

        d = {"name": name, "genres": genres}
        dfs.append(pd.DataFrame(d))
        offset += 50

    df = pd.concat(dfs)
    return df

def get_most_common_genre(df_genres):
    """ Calculates most frequently ocurring genre from a genres column """
    genres = df_genres.explode()
    
    mcs = Counter(genres).most_common(5)
    
    for mc in mcs:
        if pd.isnull(mc[0]):
            pass
        else:
            most_common = mc
            break
    
    return most_common[0]

def get_most_common_genres(df_genres):
    """ Calculates most frequently ocurring genres from a genres column """  
    mcs = Counter(df_genres).most_common(15)
    
    return mcs

def get_top_tracks(user, limit_step=1):   
    """ Returns user's most played tracks """
    name, popularity, release_date, track_uri, artist_name, artist_uri = [], [], [], [], [], []
    for offset in range(0, 10000000, limit_step):
        response = user.current_user_top_tracks(
            limit=limit_step,
            offset=offset,
        )
        if response['items'] == []:
            break
        name.append(response['items'][0]['name'])
        popularity.append(response['items'][0]['popularity'])
        release_date.append(response['items'][0]['album']['release_date'])
        track_uri.append(response['items'][0]['uri'])
        artist_name.append(response['items'][0]['artists'][0]['name']) 
        artist_uri.append(response['items'][0]['artists'][0]['uri']) 

    
    d = {"name": name, "popularity": popularity, "release_date": release_date, "track_uri": track_uri, "artist_name": artist_name, "artist_uri": artist_uri}
    df = pd.DataFrame(d)

    df['genres'] = df.artist_uri.apply(get_genres, sp=user)

    return df

def get_top_artists(user, limit_step=1):
    """ Returns user's most played artists """
    name, genres = [], []
    response = user.current_user_top_artists(limit=50)
    
    if response['items'] != []:
        
        for artist in response['items']:
            name.append(artist['name'])
            genres.append(artist['genres'])
        
    d = {"name": name, "genres": genres}
    df = pd.DataFrame(d)

    return df 

def transform(what):
    """ Transforms data for Flourish consumption """

    source_string = acct1_credentials.target_dir + what + '.csv'
    target_string_1 = acct1_credentials.target_dir + '/flourish/' + what + '_pctg.csv'
    target_string_2 = acct1_credentials.target_dir + '/flourish/' + what + '_mcg.csv'

    df = pd.read_csv(source_string, converters={'genres': literal_eval})
    df.fillna('Otro', inplace=True)
    df = df.replace({'supergenre': {  
                                        'urban': 'Urban', 
                                        'art_chamber': 'Art Chamber',
                                        'metropolis': 'Metropolis',
                                        'electronic': 'Electronic',
                                        'alt_rock': 'Alt Rock',
                                        'caribbean': 'Caribbean',
                                        'emo': 'Emo'
                                    }})

    total = len(df.index)
    df_counts = df.groupby(['supergenre'], dropna=False)['supergenre'].count()
    top_pcntg = df_counts / total
    top_pcntg.to_csv(target_string_1)

    df_non_sg = df[df['supergenre'] == 'Otro']
    genres = df_non_sg.genres.sum()
    mcg = get_most_common_genres(genres)
    mcg_df = pd.DataFrame(mcg, columns =['Genre', 'Recurrence'])
    mcg_df.to_csv(target_string_2)

def combine():
    source_dir = acct1_credentials.target_dir + '/flourish/'
    dfs = []

    for filename in os.listdir(source_dir):
        print('the filename is ' + filename)
        if(filename.endswith('_mcg.csv')):
            df = pd.read_csv(source_dir + filename)
            found = re.search('(.+?)_mcg.csv', filename).group(1)
            df['source'] = found
            dfs.append(df)

    dfs = pd.concat(dfs)
    dfs.to_csv(source_dir + 'all_mcg.csv')



def main():

    scope = "user-follow-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct1_credentials.client_ID, client_secret= acct1_credentials.client_SECRET, redirect_uri=acct1_credentials.redirect_url, scope=scope))

    # lists of identified supergenres
    urban       = ['alternative hip hop', 'hip hop', 'rap', 'underground hip hop', 'experimental hip hop', 'abstract hip hop', 'conscious hip hop', 'east coast hip hop', 'boom bap', 'psychedelic hip hop', 'trip hop', 'urbano espanol']
    art_chamber = ['art pop', 'chamber pop']
    metropolis  = ['escape room', 'pop', 'dance pop', 'electropop', 'uk pop', 'metropopolis', 'dream pop', 'hyperpop', 'experimental pop', 'proto-hyperpop', 'indietronica']
    electronic  = ['electronica', 'uk bass', 'deconstructed club', 'wonky', 'witch house', 'microhouse', 'intelligent dance music', 'fluxwork', 'grave wave', 'hauntology', 'classic dubstep', 'jungle', 'glitchbreak', 'atmospheric dnb', 'wave', 'future garage', 'new rave', 'ambient', 'alternative dance', 'uk experimental electronic', 'big beat', 'latintronica']
    alt_rock    = ['indie rock', 'alternative rock', 'rock', 'post-rock', 'experimental rock']
    caribbean   = ['dancehall', 'reggae fusion', 'traphall', 'jamaican hip hop']
    emo         = ['emo', 'dreamo', 'alternative emo', 'midwest emo', 'lo-fi emo', 'emo rap', '5th Wave Emo']

    supergenres = {
        'urban' : urban,
        'art_chamber' : art_chamber,
        'metropolis' : metropolis,
        'electronic' : electronic,
        'alt_rock' : alt_rock,
        'caribbean' : caribbean,
        'emo' : emo
    }
    
    # get saved tracks
    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct1_credentials.client_ID, client_secret= acct1_credentials.client_SECRET, redirect_uri=acct1_credentials.redirect_url, scope=scope))
    saved_tracks = get_all_saved_tracks(sp)
    saved_tracks['genres'] = saved_tracks.artist_uri.apply(get_genres, sp=sp)
    saved_tracks = add_match_and_supergenre(saved_tracks, supergenres)
    saved_tracks.to_csv(acct1_credentials.target_dir + 'saved_tracks.csv')

    # get saved albums
    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct1_credentials.client_ID, client_secret= acct1_credentials.client_SECRET, redirect_uri=acct1_credentials.redirect_url, scope=scope))
    saved_albums = get_saved_albums(sp)
    saved_albums = add_match_and_supergenre(saved_albums, supergenres)
    saved_albums.to_csv(acct1_credentials.target_dir + 'saved_albums.csv')

    # get followed artists 
    scope = "user-follow-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct1_credentials.client_ID, client_secret= acct1_credentials.client_SECRET, redirect_uri=acct1_credentials.redirect_url, scope=scope))
    followed_artists = get_followed_artists(sp)
    followed_artists = add_match_and_supergenre(followed_artists, supergenres)
    followed_artists.to_csv(acct1_credentials.target_dir + 'followed_artists.csv')

    # get top tracks
    scope = "user-top-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct1_credentials.client_ID, client_secret= acct1_credentials.client_SECRET, redirect_uri=acct1_credentials.redirect_url, scope=scope))
    top_tracks = get_top_tracks(sp)
    top_tracks = add_match_and_supergenre(top_tracks, supergenres)
    top_tracks.to_csv(acct1_credentials.target_dir + 'top_tracks.csv')

    # get top artists
    scope = "user-top-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct1_credentials.client_ID, client_secret= acct1_credentials.client_SECRET, redirect_uri=acct1_credentials.redirect_url, scope=scope))
    top_artists = get_top_artists(sp)
    top_artists = add_match_and_supergenre(top_artists, supergenres)
    top_artists.to_csv(acct1_credentials.target_dir + 'top_artists.csv')

    # ------------ analysis of recommendations starts here ------------------- #

    # playlists 
    discover_weeklies = get_playlists(sp, regex="^DW.*$")
    discover_weeklies = add_match_and_supergenre(discover_weeklies, supergenres)
    discover_weeklies.to_csv(acct1_credentials.target_dir + 'discover_weeklies.csv')
    dw_most_common_genres = discover_weeklies.groupby('name').agg({'genres': get_most_common_genre})
    dw_most_common_genres.to_csv(acct1_credentials.target_dir + 'dw_most_common_genres.csv')
    dw_match_percentages = get_match_percentage(discover_weeklies)
    dw_match_percentages.to_csv(acct1_credentials.target_dir + 'dw_match_percentages.csv')

    # daily mixes
    daily_mixes = get_playlists(sp, regex="^Daily.*$")
    daily_mixes = add_match_and_supergenre(daily_mixes, supergenres)
    daily_mixes.to_csv(acct1_credentials.target_dir + 'daily_mixes.csv')
    dm_most_common_genres = daily_mixes.groupby('name').agg({'genres': get_most_common_genre})
    dm_most_common_genres.to_csv(acct1_credentials.target_dir + 'dm_most_common_genres.csv')
    dm_match_percentages = get_match_percentage(daily_mixes)
    dm_match_percentages.to_csv(acct1_credentials.target_dir + 'dm_match_percentages.csv')

    # release radar
    release_radar = get_playlists(sp, regex="^Release.*$")
    release_radar = add_match_and_supergenre(release_radar, supergenres)
    release_radar.to_csv(acct1_credentials.target_dir + 'release_radar.csv')
    rr_most_common_genres = release_radar.groupby('name').agg({'genres': get_most_common_genre})
    rr_most_common_genres.to_csv(acct1_credentials.target_dir + 'rr_most_common_genres.csv')
    rr_match_percentages = get_match_percentage(release_radar)
    rr_match_percentages.to_csv(acct1_credentials.target_dir + 'rr_match_percentages.csv')

    # for vizualization in Flourish
    transform('saved_tracks')
    transform('saved_albums')
    transform('followed_artists')
    transform('top_tracks')
    transform('top_artists')

    # combine most common non-supergenre genres datasets
    combine()

if __name__=="__main__":
    main()
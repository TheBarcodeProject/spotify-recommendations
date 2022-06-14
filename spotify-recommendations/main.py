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

def get_features(df, genre_list):
    for genre in genre_list.index:
        df[genre] = df.apply(lambda x: 1 if genre in x['genres'] else 0, axis = 1)

    return df

def calculate_clusters(df):
    """
    Implements K means on frequencies dataframe
    """      
    features = df.iloc[:,7:] 
    kmeans = KMeans(6) 

    #print(features)

    identified_clusters = kmeans.fit_predict(features)

    df_clusters = df.copy()
    df_clusters['Cluster'] = identified_clusters 
    df_clusters = df_clusters[['name', 'Cluster']]

    #df.set_index('index', inplace=True) # Set index

    return (df, df_clusters, features)


def main():

    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=acct1_credentials.client_ID, client_secret= acct1_credentials.client_SECRET, redirect_uri=acct1_credentials.redirect_url, scope=scope))
    print("success!")
    liked_tracks_df = get_all_saved_tracks(sp)
    #liked_tracks_df['genres'] = liked_tracks_df['artist_uri'].apply(get_genres, sp = sp)

    #liked_artists_df = liked_tracks_df.groupby(['artist_name'])['artist_name'].count()

    #liked_genres_df = get_genre_counts(liked_tracks_df)

    #features = get_features(liked_tracks_df, liked_genres_df)

    #features.to_csv("test.csv", mode='w+')

    #df_clusters = calculate_clusters(features)[1]

    print(liked_tracks_df)


if __name__=="__main__":
    main()
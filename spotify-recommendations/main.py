import spotipy
from spotipy.oauth2 import SpotifyOAuth
import credentials
import pandas as pd

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

def main():

    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=credentials.client_ID, client_secret= credentials.client_SECRET, redirect_uri=credentials.redirect_url, scope=scope))

    liked_tracks_df = get_all_saved_tracks(sp)


if __name__=="__main__":
    main()
import json
import requests

def fetch_xtream_live_channels(host, username, password):
    base_url = f"{host}/player_api.php?username={username}&password={password}"
    response = requests.get(f"{base_url}&action=get_live_categories")
    categories = response.json()

    playlist = []
    for category in categories:
        streams = requests.get(f"{base_url}&action=get_live_streams&category_id={category['category_id']}").json()
        playlist.extend([f"#EXTINF:-1,{stream['name']}\n{stream['stream_url']}" for stream in streams])

    return playlist

def main():
    with open("xtream_login.json", "r") as file:
        credentials = json.load(file)

    if "username" in credentials:
        playlist = fetch_xtream_live_channels(credentials["host"], credentials["username"], credentials["password"])
    else:
        raise ValueError("Invalid credentials in xtream_login.json")

    with open("filtered_playlist.m3u", "w") as file:
        file.writelines("\n".join(playlist))

if __name__ == "__main__":
    main()

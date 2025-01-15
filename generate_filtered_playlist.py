import json
import requests


def fetch_playlist(credentials):
    host = credentials["host"]

    if "username" in credentials and "password" in credentials:
        username = credentials["username"]
        password = credentials["password"]
        url = f"{host}/player_api.php?username={username}&password={password}&action=get_live_categories"
    elif "mac_address" in credentials:
        mac_address = credentials["mac_address"]
        url = f"{host}/server/load.php?mac={mac_address}&type=stb&action=get_live_categories"
    else:
        raise ValueError("Invalid credentials format.")

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch categories.")

    return response.json()


def save_playlist(categories, filename):
    allowed_groups = ["INDIA", "INDIAN", "TELUGU", "CRICKET"]
    playlist = []

    for category in categories:
        if category["category_name"] in allowed_groups:
            playlist.append(f"#EXTINF:-1, {category['category_name']}")

    with open(filename, "w") as f:
        f.write("\n".join(playlist))


if __name__ == "__main__":
    with open("xtream_login.json", "r") as f:
        credentials = json.load(f)

    categories = fetch_playlist(credentials)
    save_playlist(categories, "filtered_playlist.m3u")

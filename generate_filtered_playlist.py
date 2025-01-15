import json
import requests


def fetch_xtream_live_channels(host, username, password, allowed_groups):
    """Fetch live channels using Xtream API."""
    base_url = f"{host}/player_api.php?username={username}&password={password}"

    # Fetch all live categories
    categories_url = f"{base_url}&action=get_live_categories"
    categories_response = requests.get(categories_url)

    if categories_response.status_code != 200:
        raise Exception("Failed to fetch categories. Check your Xtream credentials.")

    categories = categories_response.json()
    playlist = []

    for category in categories:
        category_name = category["category_name"]

        # Check if the category name is allowed
        if not (category_name in allowed_groups or category_name.startswith("IND")):
            continue

        category_id = category["category_id"]

        # Fetch streams for the current category
        streams_url = f"{base_url}&action=get_live_streams&category_id={category_id}"
        streams_response = requests.get(streams_url)

        if streams_response.status_code != 200:
            print(f"Failed to fetch streams for category: {category_name}")
            continue

        streams = streams_response.json()

        # Add category header
        playlist.append(f"# Group: {category_name}")

        # Add streams to the playlist
        for stream in streams:
            stream_name = stream["name"]
            stream_id = stream["stream_id"]
            stream_icon = stream.get("stream_icon", "")
            stream_url = f"{host}/live/{username}/{password}/{stream_id}.m3u8"

            # Add stream details to the playlist
            playlist.append(
                f"#EXTINF:-1 tvg-logo=\"{stream_icon}\" group-title=\"{category_name}\",{stream_name}"
            )
            playlist.append(stream_url)

    return playlist


def fetch_stalker_live_channels(host, mac_address, allowed_groups):
    """Fetch live channels using Stalker Portal."""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": host,
        "X-User-Agent": "Model: MAG254; Link: Ethernet",
    }

    # Login to Stalker Portal
    login_url = f"{host}/server/load.php?type=stb&action=handshake&JsHttpRequest=1-xml"
    login_response = requests.get(login_url, headers=headers)

    if login_response.status_code != 200:
        raise Exception("Failed to connect to the Stalker Portal.")

    token = login_response.json().get("js", {}).get("token")
    if not token:
        raise Exception("Failed to retrieve token from Stalker Portal.")

    headers["Authorization"] = f"Bearer {token}"
    headers["mac"] = mac_address

    # Fetch all live categories
    categories_url = f"{host}/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
    categories_response = requests.get(categories_url, headers=headers)

    if categories_response.status_code != 200:
        raise Exception("Failed to fetch channels from Stalker Portal.")

    channels = categories_response.json().get("js", {}).get("data", [])
    playlist = []

    for channel in channels:
        category_name = channel.get("tv_genre", "Unknown")

        # Check if the category name is allowed
        if not (category_name in allowed_groups or category_name.startswith("IND")):
            continue

        stream_name = channel.get("name", "Unknown")
        stream_url = channel.get("cmd")
        stream_icon = channel.get("logo", "")

        # Add stream details to the playlist
        playlist.append(
            f"#EXTINF:-1 tvg-logo=\"{stream_icon}\" group-title=\"{category_name}\",{stream_name}"
        )
        playlist.append(stream_url)

    return playlist


# Load credentials from xtream_login.json
with open("xtream_login.json", "r") as file:
    credentials = json.load(file)

host = credentials["host"]
allowed_groups = ["INDIA", "INDIAN", "TELUGU", "CRICKET", "IN"]

# Check the type of credentials
if "username" in credentials and "password" in credentials:
    # Xtream credentials
    username = credentials["username"]
    password = credentials["password"]
    playlist = fetch_xtream_live_channels(host, username, password, allowed_groups)
elif "mac_address" in credentials:
    # Stalker Portal credentials
    mac_address = credentials["mac_address"]
    playlist = fetch_stalker_live_channels(host, mac_address, allowed_groups)
else:
    raise Exception("Invalid credentials format in xtream_login.json")

# Save the playlist to a file
with open("filtered_playlist.m3u", "w") as file:
    file.write("\n".join(playlist))

print("Playlist generated successfully!")

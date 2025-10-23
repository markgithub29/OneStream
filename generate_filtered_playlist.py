import json
import requests

def is_xtream_portal(host):
    """Check if the host supports Xtream Codes API."""
    test_url = f"{host.rstrip('/')}/player_api.php?username=test&password=test"
    try:
        response = requests.get(test_url, timeout=6)
        if response.status_code == 200 and "user_info" in response.text:
            print(f"✅ Xtream API detected: {host}")
            return True
    except Exception:
        pass
    print(f"❌ Xtream API not detected at {test_url}")
    return False


def fetch_xtream_live_channels(host, username, password, allowed_groups):
    """Fetch live channels using Xtream API."""
    base_url = f"{host.rstrip('/')}/player_api.php?username={username}&password={password}"

    # Fetch all live categories
    categories_url = f"{base_url}&action=get_live_categories"
    categories_response = requests.get(categories_url, timeout=10)

    if categories_response.status_code != 200:
        raise Exception("Failed to fetch categories. Check Xtream credentials.")

    try:
        categories = categories_response.json()
    except Exception:
        raise Exception(f"Invalid JSON response from Xtream API: {categories_response.text[:200]}")

    playlist = []
    for category in categories:
        category_name = category["category_name"]

        # Filter allowed categories
        if not (category_name in allowed_groups or category_name.startswith("IND")):
            continue

        category_id = category["category_id"]
        streams_url = f"{base_url}&action=get_live_streams&category_id={category_id}"
        streams_response = requests.get(streams_url, timeout=10)

        if streams_response.status_code != 200:
            print(f"Failed to fetch streams for category: {category_name}")
            continue

        try:
            streams = streams_response.json()
        except Exception:
            print(f"Invalid stream response for category: {category_name}")
            continue

        playlist.append(f"# Group: {category_name}")
        for stream in streams:
            stream_name = stream.get("name", "Unknown")
            stream_id = stream.get("stream_id", "")
            stream_icon = stream.get("stream_icon", "")
            stream_url = f"{host.rstrip('/')}/live/{username}/{password}/{stream_id}.m3u8"

            playlist.append(f"#EXTINF:-1 tvg-logo=\"{stream_icon}\" group-title=\"{category_name}\",{stream_name}")
            playlist.append(stream_url)

    return playlist


def fetch_stalker_live_channels(host, mac_address, allowed_groups):
    """Fetch live channels using Stalker Portal (auto-detects path)."""
    possible_paths = ["", "/c", "/portal", "/stalker_portal"]
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": host,
        "X-User-Agent": "Model: MAG254; Link: Ethernet",
    }

    token = None
    valid_host = None

    for path in possible_paths:
        login_url = f"{host.rstrip('/')}{path}/server/load.php?type=stb&action=handshake&JsHttpRequest=1-xml"
        print(f"Trying portal: {login_url}")
        try:
            login_response = requests.get(login_url, headers=headers, timeout=10)
        except Exception as e:
            print(f"Connection failed for {login_url}: {e}")
            continue

        if login_response.status_code != 200:
            print(f"Invalid response ({login_response.status_code}) for {login_url}")
            continue

        try:
            data = login_response.json()
            token = data.get("js", {}).get("token")
            if token:
                valid_host = f"{host.rstrip('/')}{path}"
                print(f"✅ Found valid Stalker portal: {valid_host}")
                break
        except Exception:
            print(f"Non-JSON response for {login_url}: {login_response.text[:200]}")

    if not token:
        raise Exception("❌ Failed to detect valid Stalker Portal or get token.")

    headers["Authorization"] = f"Bearer {token}"
    headers["mac"] = mac_address

    channels_url = f"{valid_host}/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
    print(f"Fetching channels from: {channels_url}")
    channels_response = requests.get(channels_url, headers=headers, timeout=10)

    if channels_response.status_code != 200:
        raise Exception("Failed to fetch channels from Stalker Portal.")

    try:
        channels = channels_response.json().get("js", {}).get("data", [])
    except Exception:
        print("Invalid JSON from channel fetch:")
        print(channels_response.text[:200])
        raise Exception("Stalker channel fetch returned invalid JSON.")

    playlist = []
    for channel in channels:
        category_name = channel.get("tv_genre", "Unknown")

        if not (category_name in allowed_groups or category_name.startswith("IND")):
            continue

        stream_name = channel.get("name", "Unknown")
        stream_url = channel.get("cmd")
        stream_icon = channel.get("logo", "")

        playlist.append(f"#EXTINF:-1 tvg-logo=\"{stream_icon}\" group-title=\"{category_name}\",{stream_name}")
        playlist.append(stream_url)

    return playlist


# Main logic
with open("xtream_login.json", "r") as file:
    credentials = json.load(file)

host = credentials["host"].rstrip("/")
allowed_groups = ["INDIA", "INDIAN", "TELUGU", "CRICKET"]

try:
    if is_xtream_portal(host):
        if "username" not in credentials or "password" not in credentials:
            raise Exception("Xtream portal detected but username/password missing.")
        playlist = fetch_xtream_live_channels(host, credentials["username"], credentials["password"], allowed_groups)
    else:
        if "mac_address" not in credentials:
            raise Exception("Stalker portal detected but MAC address missing.")
        playlist = fetch_stalker_live_channels(host, credentials["mac_address"], allowed_groups)

    with open("filtered_playlist.m3u", "w", encoding="utf-8") as file:
        file.write("\n".join(playlist))

    print("\n✅ Playlist generated successfully!")

except Exception as e:
    print(f"\n❌ Error: {e}")

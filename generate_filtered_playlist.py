import json
import requests
import sys

def fetch_xtream_live_channels(host, username, password, allowed_groups):
    """Fetch live channels using Xtream API."""
    print(f"🎯 Using Xtream API: {host}")
    base_url = f"{host}/player_api.php?username={username}&password={password}"

    try:
        # Fetch all live categories
        categories_url = f"{base_url}&action=get_live_categories"
        categories_response = requests.get(categories_url, timeout=10)

        if categories_response.status_code != 200:
            raise Exception("Failed to fetch categories.")

        categories = categories_response.json()
        playlist = []

        for category in categories:
            category_name = category.get("category_name", "")
            category_id = category.get("category_id")

            if not (category_name in allowed_groups or category_name.startswith("IND")):
                continue

            streams_url = f"{base_url}&action=get_live_streams&category_id={category_id}"
            streams_response = requests.get(streams_url, timeout=10)

            if streams_response.status_code != 200:
                print(f"⚠️ Failed to fetch streams for {category_name}")
                continue

            streams = streams_response.json()

            # Add category header
            playlist.append(f"# Group: {category_name}")

            for stream in streams:
                stream_name = stream.get("name", "Unknown")
                stream_id = stream.get("stream_id")
                stream_icon = stream.get("stream_icon", "")
                stream_url = f"{host}/live/{username}/{password}/{stream_id}.m3u8"

                playlist.append(
                    f"#EXTINF:-1 tvg-logo=\"{stream_icon}\" group-title=\"{category_name}\",{stream_name}"
                )
                playlist.append(stream_url)

        return playlist

    except Exception as e:
        raise Exception(f"Xtream fetch failed: {e}")


def fetch_stalker_live_channels(host, mac_address, allowed_groups):
    """Fetch live channels using Stalker Portal."""
    print(f"🎯 Using Stalker Portal: {host}")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": host,
        "X-User-Agent": "Model: MAG254; Link: Ethernet",
        "mac": mac_address,
    }

    try:
        # Try multiple possible handshake endpoints
        portals = [
            f"{host}/server/load.php?type=stb&action=handshake&JsHttpRequest=1-xml",
            f"{host}/portal/server/load.php?type=stb&action=handshake&JsHttpRequest=1-xml",
            f"{host}/c/server/load.php?type=stb&action=handshake&JsHttpRequest=1-xml",
        ]

        token = None
        for portal in portals:
            print(f"Trying portal: {portal}")
            r = requests.get(portal, headers=headers, timeout=10)
            try:
                data = r.json()
                token = data.get("js", {}).get("token")
                if token:
                    break
            except Exception:
                print(f"Non-JSON response for {portal}")

        if not token:
            raise Exception("❌ Failed to detect valid Stalker Portal or get token.")

        headers["Authorization"] = f"Bearer {token}"

        channels_url = f"{host}/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
        channels_response = requests.get(channels_url, headers=headers, timeout=10)

        if channels_response.status_code != 200:
            raise Exception("Failed to fetch channels list.")

        data = channels_response.json()
        channels = data.get("js", {}).get("data", [])
        playlist = []

        for channel in channels:
            category_name = channel.get("tv_genre", "Unknown")

            if not (category_name in allowed_groups or category_name.startswith("IND")):
                continue

            stream_name = channel.get("name", "Unknown")
            stream_icon = channel.get("logo", "")
            stream_url = channel.get("cmd", "")

            playlist.append(
                f"#EXTINF:-1 tvg-logo=\"{stream_icon}\" group-title=\"{category_name}\",{stream_name}"
            )
            playlist.append(stream_url)

        return playlist

    except Exception as e:
        raise Exception(f"Stalker fetch failed: {e}")


# ------------------ MAIN EXECUTION ------------------ #
try:
    with open("xtream_login.json", "r") as file:
        credentials = json.load(file)

    host = credentials.get("host")
    if not host:
        raise Exception("❌ Host not defined in xtream_login.json")

    allowed_groups = ["INDIA", "INDIAN", "TELUGU", "CRICKET"]

    if "username" in credentials and "password" in credentials:
        playlist = fetch_xtream_live_channels(
            host, credentials["username"], credentials["password"], allowed_groups
        )
    elif "mac_address" in credentials:
        playlist = fetch_stalker_live_channels(
            host, credentials["mac_address"], allowed_groups
        )
    else:
        raise Exception("❌ Invalid credentials format in xtream_login.json")

    if not playlist:
        raise Exception("No channels found.")

    with open("filtered_playlist.m3u", "w", encoding="utf-8") as file:
        file.write("\n".join(playlist))

    print("✅ Playlist generated successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

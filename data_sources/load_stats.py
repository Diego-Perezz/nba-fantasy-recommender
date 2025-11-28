import os
import time
import json
import yaml
import requests
from pathlib import Path


# Load API config 
def load_config():
    config_path = Path(__file__).resolve().parent / "api_config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


config = load_config()
nba_cfg = config["nba_stats"]
settings = config["settings"]

BASE_URL = nba_cfg["base_url"]
HEADERS = nba_cfg["headers"]
ENDPOINTS = nba_cfg["endpoints"]
DEFAULT_PARAMS = nba_cfg["default_params"]



# Helper: Build endpoint URL
def build_url(endpoint_name):
    if endpoint_name not in ENDPOINTS:
        raise ValueError(f"Unknown endpoint: {endpoint_name}")
    return f"{BASE_URL}/{ENDPOINTS[endpoint_name]}"



# Helper: Make request with retry logic
def fetch_json(url, params):
    retries = settings["retries"]

    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=settings["timeout"])

            if response.status_code == 200:
                return response.json()

            print(f"[WARNING] Status {response.status_code} on attempt {attempt+1}/{retries}")

        except Exception as e:
            print(f"[ERROR] Exception: {e} (attempt {attempt+1}/{retries})")

        time.sleep(settings["sleep_between_calls"])

    raise RuntimeError(f"Failed to fetch data after {retries} attempts from: {url}")



# Save JSON to raw_data/stats_json/
def save_json(data, filename):
    raw_dir = Path(__file__).resolve().parents[1] / "raw_data" / "stats_json"
    raw_dir.mkdir(parents=True, exist_ok=True)

    path = raw_dir / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[SUCCESS] Saved data to {path}")


# Fetch season player stats
def load_season_player_stats(season=None):
    url = build_url("season_player_stats")
    params = DEFAULT_PARAMS.copy()

    if season:
        params["Season"] = season  # override season manually if needed

    data = fetch_json(url, params)
    save_json(data, "season_player_stats.json")
    return data



# Fetch game logs for a specific player
def load_player_game_logs(player_id, season=None):
    url = build_url("player_game_logs")
    params = DEFAULT_PARAMS.copy()
    params["PlayerID"] = player_id

    if season:
        params["Season"] = season

    data = fetch_json(url, params)
    filename = f"player_game_logs_{player_id}.json"
    save_json(data, filename)
    return data



# Fetch advanced stats (same endpoint, different params)
def load_advanced_stats(season=None):
    url = build_url("advanced_stats")
    params = DEFAULT_PARAMS.copy()
    params["MeasureType"] = "Advanced"

    if season:
        params["Season"] = season

    data = fetch_json(url, params)
    save_json(data, "player_advanced_stats.json")
    return data


# Quick test when running directly
if __name__ == "__main__":
    print("Fetching season player stats...")
    load_season_player_stats()

    print("Fetching advanced stats...")
    load_advanced_stats()

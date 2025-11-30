import requests
import pandas as pd
from pathlib import Path
import json


TEAM_ID_MAP = {
    "ATL": 1, "BOS": 2, "BKN": 17, "CHA": 30, "CHI": 4, "CLE": 5,
    "DAL": 6, "DEN": 7, "DET": 8, "GSW": 9, "HOU": 10, "IND": 11,
    "LAC": 12, "LAL": 13, "MEM": 29, "MIA": 14, "MIL": 15, "MIN": 16,
    "NOP": 3, "NYK": 18, "OKC": 25, "ORL": 19, "PHI": 20, "PHX": 21,
    "POR": 22, "SAC": 23, "SAS": 24, "TOR": 28, "UTA": 26, "WSH": 27
}


def save_json(data, filename):
    raw_dir = Path(__file__).resolve().parents[1] / "raw_data" / "injuries_json"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / filename

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[SUCCESS] Saved JSON to {path}")


def fetch_team_injuries(team_code, team_id):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{team_id}/injuries"

    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []

    data = r.json()
    items = data.get("items", [])
    players = []

    for item in items:
        # Fetch injury details
        injury_details = requests.get(item["$ref"]).json()

        # Fetch ATHLETE object
        athlete_ref = injury_details.get("athlete", {}).get("$ref")
        athlete_name = None
        athlete_pos = None

        if athlete_ref:
            athlete_data = requests.get(athlete_ref).json()
            athlete_name = athlete_data.get("displayName")
            athlete_pos = athlete_data.get("position", {}).get("abbreviation")

        players.append({
            "team": team_code,
            "player": athlete_name,
            "position": athlete_pos,
            "status": injury_details.get("status"),
            "injury_type": injury_details.get("details", {}).get("type"),
            "injury_location": injury_details.get("details", {}).get("location"),
            "injury_detail": injury_details.get("details", {}).get("detail"),
            "injury_side": injury_details.get("details", {}).get("side"),
            "return_date": injury_details.get("details", {}).get("returnDate"),
            "updated": injury_details.get("date")
        })

    return players


def load_all_injuries():
    print("[INFO] Fetching ESPN team injuries via internal API...")

    all_injuries = []

    for team_code, team_id in TEAM_ID_MAP.items():
        print(f"  - {team_code}")
        items = fetch_team_injuries(team_code, team_id)
        all_injuries.extend(items)

    save_json(all_injuries, "injury_report_full.json")

    df = pd.DataFrame(all_injuries)
    print("[SUCCESS] Parsed FULL ESPN injury dataset")
    return df


if __name__ == "__main__":
    df = load_all_injuries()
    print(df.head())

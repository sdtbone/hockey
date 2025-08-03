#!/usr/bin/env python3

import json
import pprint
import pytz
import requests
from ics import Calendar, Event
from datetime import datetime, timedelta

# NHL API URL for team schedule
# Example URL format:
# https://api-web.nhle.com/v1/club-schedule-season/{TEAM}/{SEASON}

# ---- Hardcoded configuration ----
BASE_URL = "https://api-web.nhle.com/v1/club-schedule-season"  # Change to your actual base URL
TEAM = "SEA"
SEASON = "20252026"
DEBUG_MODE = True  # Set to True for debug output
LOCAL_TIMEZONE = "America/Los_Angeles"
# ---------------------------------

def get_team_schedule_url():
    url = f"{BASE_URL}/{TEAM}/{SEASON}"
    return url

def get_team_schedule():
    url = get_team_schedule_url()
    try:
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            data = json.loads(response.text)
            if DEBUG_MODE:
                debug_file = f"{TEAM}_schedule_debug.json"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            return data
    except requests.exceptions.RequestException as err:
        print(f'Error: {err}')

def create_ics(schedule):
    ics_file = f"{TEAM}_schedule.ics"
    cal = Calendar()
    games = schedule['games']

    for game in games:
        if game['gameState'] == "FUT":
            away_team = game['awayTeam']['abbrev']
            home_team = game['homeTeam']['abbrev']
            location = game['venue']['default']
            utc_start_time = datetime.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ')
            utc_time = pytz.utc.localize(utc_start_time)
            local_timezone = pytz.timezone(LOCAL_TIMEZONE)
            local_time = utc_time.astimezone(local_timezone)

           # Build event details
            event = Event()
            event.name = f"{away_team} @ {home_team}"
            event.begin = local_time
            event.duration = timedelta(hours=3)
            event.location = location

            # Add description with more info
            matchup = f"{away_team} at {home_team}"
            game_type = game.get('gameType', 'Regular Season')
            game_id = game.get('id', '')
            game_url = f"https://www.nhl.com/gamecenter/{game_id}" if game_id else ""
            description_lines = [
                f"Matchup: {matchup}",
                f"Game Type: {game_type}",
                f"Start Time (Pacific): {local_time.strftime('%Y-%m-%d %I:%M %p %Z')}",
                f"Location: {location}",
            ]
            if game_url:
                description_lines.append(f"More Info: {game_url}")
            event.description = "\n".join(description_lines)

            # Add event to calendar
            cal.events.add(event)

    with open(ics_file, 'w') as f:
        f.writelines(cal)

def main():
    schedule = get_team_schedule()
    if schedule:
        if DEBUG_MODE:
            team_schedule = f"{TEAM}_schedule.txt"
            with open(team_schedule, 'w', encoding='utf-8') as f:
                f.write(pprint.pformat(schedule))
        create_ics(schedule)

if __name__ == "__main__":
    main()
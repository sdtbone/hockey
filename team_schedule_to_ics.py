#!/usr/bin/env python3

import configparser
import json
import logging
import pprint
import pytz
import requests
from ics import Calendar, Event
from datetime import datetime, timedelta

# Initialize logging
logging.basicConfig(
    format='%(asctime)-15s %(message)s',
    datefmt='%Y/%m/%d@%H:%M:%S',
    level=logging.INFO
)


# Get our configs, maybe someday I'll create a UI but for now this will do
def get_config_value(config, section, option, default=None):
    try:
        return config.getboolean(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default


# Setup the URL we'll need to retrieve schedule info
def get_team_schedule_url(config):
    base_url = config.get('settings', 'base_url')
    team = config.get('settings', 'team')
    season = config.get('settings', 'season')
    url = base_url + '/' + team + '/' + season
    return url


# Hmmm  what does this do?? Oh gets the team schedule, doh
def get_team_schedule(config):
    url = get_team_schedule_url(config)
    try:
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            return json.loads(response.text)
    except requests.exceptions.RequestException as err:
        logging.error(f'Error: {err}')

# Create the ICS file
def create_ics(schedule, config):
    ics_file = config.get('settings', 'team') + '_schedule.ics'
    cal = Calendar()
    club_timezone = schedule['clubTimezone']
    games = schedule['games']

    for game in games:
        if game['gameState'] == "FUT":
            away_team = game['awayTeam']['abbrev']
            home_team = game['homeTeam']['abbrev']
            location = game['venue']['default']
            utc_start_time = datetime.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ')
            utc_time = pytz.utc.localize(utc_start_time)
            local_timezone = pytz.timezone('America/Los_Angeles')
            local_time = utc_time.astimezone(local_timezone)

            if home_team.upper() == config.get('settings', 'team').upper():
                event = Event()
                event.name = f"{home_team} vs. {away_team}"
                event.begin = local_time
                event.duration = timedelta(hours=3)
                event.location = location
                cal.events.add(event)

    with open(ics_file, 'w') as f:
        f.writelines(cal)

def main():
    config = configparser.ConfigParser()
    config.read('get_nhl_team_schedule.ini')

    debug_mode = get_config_value(config, 'settings', 'debug', default=False)

    if debug_mode:
        logging.getLogger().addHandler(logging.StreamHandler())

    schedule = get_team_schedule(config)
    if schedule:
        if debug_mode:
            team_schedule = config.get('settings', 'team') + '_schedule.txt'
            with open(team_schedule, 'w', encoding='utf-8') as f:
                f.write(pprint.pformat(schedule))
        create_ics(schedule, config)

if __name__ == "__main__":
    main()

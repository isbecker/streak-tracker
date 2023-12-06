import argparse
import datetime
import json
import logging
import os
from getpass import getpass
from typing import Optional

import requests
from garminconnect import (Garmin, GarminConnectAuthenticationError,
                           GarminConnectConnectionError,
                           GarminConnectTooManyRequestsError)
from garth.exc import GarthHTTPError

logging.basicConfig(level=logging.ERROR)


def logins() -> str | None:
    """Login to Garmin Connect portal and get a session token
    :return: Session token string or None
    :rtype: str or None
    """
    try:
        logging.debug("Attempting to login to Garmin Connect")
        email = input("Enter your email: ")
        password = getpass("Enter your password: ")
        # Initialize Garmin client with credentials
        garmin = Garmin(email, password)
        # Login to Garmin Connect portal
        garmin.login()

        return garmin.garth.dumps()
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
        logging.error("Error occurred during Garmin Connect Client init or login: %s" % err)
        return None

def did_i_run_today() -> bool | None:
    """Check if you ran today
    Read the token from the environment variable GARMIN_TOKENS, no other options for the token are supported
    :return: True if you ran today, False if you did not run today, None if there was an error
    :rtype: bool or None
    """

    tokens = os.environ.get("GARMIN_TOKENS", None)
    try:
        garmin = Garmin()
        garmin.garth.loads(tokens)
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        logging.debug("No token found, attempting to login")
        return None        

    # Get current date in USA/New York time zone
    today = today_in_new_york()
    
    logging.debug("Getting activities for date: {}".format(today))

    # Get running activities data
    activities = garmin.get_activities_fordate(today)
    activities = activities['ActivitiesForDay']['payload']
    # Check if there are any activities
    if len(activities) == 0:
        logging.warn("No activities found")
        return False

    logging.debug("Found {} activities".format(len(activities)))
    # Check if any of the activities were running using a functional style
    any_running = any('run' in str(activity['activityType']['typeKey']).lower() for activity in activities)

    logging.debug(activities)
    
    return any_running

def today_in_new_york() -> datetime.datetime:
    """Get today's date in New York
    :return: Today's date in New York
    :rtype: datetime.datetime
    """
    return datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-5))).date()

def write_to_streak_file() -> None:
    """Write to a file to indicate that you ran today
    """
    today = today_in_new_york().strftime("%Y-%m-%d")
    filename = "streak.json"

    # Load existing data
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        # Check if today's date is already in the file
        if any(run["date"] == today for run in data["runs"]):
            return
        data["total_count"] += 1
        data["runs"].append({"date": today})
    else:
        data = {
            "total_count": 1,
            "runs": [{"date": today}]
        }

    # Write the updated data
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)



def populate_streak_file(since: datetime.date) -> None:
    """Populate the streak file with dates since a specified date
    :param since: Date to start populating the streak file from
    :type since: datetime.date
    :return: None
    """
    start_date = since
    end_date = datetime.datetime.now().date()
    delta = datetime.timedelta(days=1)
    filename = "streak.json"

    # Initialize data
    data = {
        "total_count": 0,
        "runs": []
    }

    # If file exists, load existing data
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)

    # Populate data
    while start_date <= end_date:
        date_str = start_date.strftime("%Y-%m-%d")
        if not any(run["date"] == date_str for run in data["runs"]):
            data["total_count"] += 1
            data["runs"].append({"date": date_str})
        start_date += delta

    # Write data to file
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    # Parse command line arguments
    argparse = argparse.ArgumentParser()
    argparse.add_argument("--login", action="store_true")

    # add argument to populate streak file since a specified date
    argparse.add_argument("--populate", action="store_true")
    argparse.add_argument("--date", type=str, default="2021-12-26")

    args = argparse.parse_args()
    
    if args.login:
        if tokens := logins():
            print(f"""
Login successful!
Set the environment variable GARMIN_TOKENS to the above value to avoid logging in again.
For example, in bash, run:
export GARMIN_TOKENS='{tokens}'

You can also add it to an .env.local file in the root of this project.
            """.strip())
        exit(0)
    
    if args.populate:
        populate_streak_file(datetime.datetime.strptime(args.date, "%Y-%m-%d").date())
        exit(0)

    ran_today = did_i_run_today()
    if ran_today:
        logging.info("You ran today!")
        write_to_streak_file()
    else:
        logging.warn("You did not run today")


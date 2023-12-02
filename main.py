from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)
from garth.exc import GarthHTTPError

from getpass import getpass
from typing import Optional
import datetime
import logging
import requests
import os
import argparse

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

    # Get running activities data
    # Get current date
    today = datetime.date.today()
    
    logging.debug("Getting activities for date: {}".format(today))

    activities = garmin.get_activities_fordate(today)
    activities = activities['ActivitiesForDay']['payload']
    # Check if there are any activities
    if len(activities) == 0:
        print("No activities found")
        return False

    logging.debug("Found {} activities".format(len(activities)))
    # Check if any of the activities were running using a functional style
    any_running = any('run' in activity['activityType']['typeKey'] for activity in activities)

    logging.debug(activities)
    
    return any_running

if __name__ == "__main__":
    # use argparse and add a --login flag to login and save the token
    argparse = argparse.ArgumentParser()
    argparse.add_argument("--login", action="store_true")
    args = argparse.parse_args()
    
    if args.login:
        tokens = logins()
        if tokens:
            print(tokens)
        exit(0)

    ran_today = did_i_run_today()
    if ran_today:
        print("You ran today!")
    else:
        print("You did not run today")


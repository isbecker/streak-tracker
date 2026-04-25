import argparse
import datetime
import json
import logging
import os
import sys
from getpass import getpass
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Optional

import requests
from garminconnect import (Garmin, GarminConnectAuthenticationError,
                           GarminConnectConnectionError,
                           GarminConnectTooManyRequestsError)

logging.basicConfig(level=logging.ERROR)

class Config:
    """Configuration class for the Garmin Connect API demo."""

    def __init__(self):
        # Load environment variables
        self.email = os.getenv("GARMIN_EMAIL") or os.getenv("EMAIL")
        self.password = os.getenv("GARMIN_PASSWORD") or os.getenv("PASSWORD")
        self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"

        # Date settings
        self.today = datetime.date.today()
        self.week_start = self.today - timedelta(days=7)
        self.month_start = self.today - timedelta(days=30)

        # API call settings
        self.default_limit = 100
        self.start = 0
        self.start_badge = 1  # Badge related calls start counting at 1

        # Activity settings
        self.activitytype = ""  # Possible values: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
        self.activityfile = "test_data/*.gpx"  # Supported file types: .fit .gpx .tcx
        self.workoutfile = "test_data/sample_workout.json"  # Sample workout JSON file

        # Export settings
        self.export_dir = Path("your_data")
        self.export_dir.mkdir(exist_ok=True)

config = Config()

def get_mfa() -> str:
    """Get MFA token."""
    return input("MFA one-time code: ")

def init_api(email: str | None = None, password: str | None = None) -> Garmin | None:
    """Initialize Garmin API with smart error handling and recovery."""
    # First try to login with stored tokens
    try:
        print(f"Attempting to login using stored tokens from: {config.tokenstore}")

        garmin = Garmin()
        garmin.login("~/.garminconnect")
        print("Successfully logged in using stored tokens!")
        return garmin

    except GarminConnectTooManyRequestsError as err:
        print(f"\n❌ {err}")
        sys.exit(1)

    except (
        FileNotFoundError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ):
        print("No valid tokens found. Requesting fresh login credentials.")

    # Loop for credential entry with retry on auth failure
    while True:
        try:
            # Get credentials if not provided
            if not email or not password:
                email = input("Email address: ").strip()
                password = getpass("Password: ")

            print("Logging in with credentials...")
            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()

            if result1 == "needs_mfa":
                print("Multi-factor authentication required")

                mfa_code = get_mfa()
                print("🔄 Submitting MFA code...")

                try:
                    garmin.resume_login(result2, mfa_code)
                    print("✅ MFA authentication successful!")

                except GarminConnectTooManyRequestsError:
                    print("❌ Too many MFA attempts")
                    print("💡 Please wait 30 minutes before trying again")
                    sys.exit(1)
                except GarminConnectAuthenticationError as mfa_error:
                    # Handle specific errors from MFA
                    error_str = str(mfa_error)
                    print(f"🔍 Debug: MFA error details: {error_str}")
                    if "401" in error_str or "403" in error_str:
                        print("❌ Invalid MFA code")
                        print("💡 Please verify your MFA code and try again")
                        continue
                    # Other HTTP errors - don't retry
                    print(f"❌ MFA authentication failed: {mfa_error}")
                    sys.exit(1)

            # Save tokens for future use
            garmin.client.dump(config.tokenstore)
            print(f"Login successful! Tokens saved to: {config.tokenstore}")

            return garmin

        except GarminConnectTooManyRequestsError as err:
            print(f"\n❌ {err}")
            sys.exit(1)

        except GarminConnectAuthenticationError as err:
            print(f"\n❌ {err}")
            print("💡 Please check your username and password and try again")
            # Clear the provided credentials to force re-entry
            email = None
            password = None
            continue

        except (
            FileNotFoundError,
            GarminConnectConnectionError,
            requests.exceptions.HTTPError,
        ) as err:
            print(f"❌ Connection error: {err}")
            print("💡 Please check your internet connection and try again")
            return None

        except KeyboardInterrupt:
            print("\nLogin cancelled by user")
            return None

def logins() -> str | None:
    """Login to Garmin Connect portal and get a session token
    :return: Session token string or None
    :rtype: str or None
    """
    try:
        logging.debug("Attempting to login to Garmin Connect")
        # email = input("Enter your email: ")
        # password = getpass("Enter your password: ")
        # Initialize Garmin client with credentials
        garmin = init_api()


        return garmin.client.dumps()
    except (FileNotFoundError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
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
        garmin.client.loads(tokens)
    except (FileNotFoundError, GarminConnectAuthenticationError):
        logging.debug("No token found, attempting to login")
        return None        

    # Get current date in USA/New York time zone
    today = today_in_new_york()
    
    logging.debug("Getting activities for date: {}".format(today))

    # Get running activities data
    activities = garmin.get_activities_fordate(today.isoformat())
    activities = activities['ActivitiesForDay']['payload']
    # Check if there are any activities
    if len(activities) == 0:
        logging.warning("No activities found")
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
        logging.warning("You did not run today")


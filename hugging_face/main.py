import datetime
import time
from read_mail import store_in_mongodb, get_interview_data, mail
import os
from playwright.sync_api import sync_playwright
# from testing import *
from bot_login import *

def main():
    while True:
        print("Fetching and processing emails...")
        mail()
        time.sleep(10)

        print("Checking for interviews...")
        interview_data = get_interview_data()
        for item in interview_data:
            names_emails = item.get("names_emails", [])
            names = []

            if names_emails:
                for person in names_emails:
                    name = person.get("name", "No name")
                    names.append(name)

            title = item.get("meeting_title", "No title")
            interview_id = item.get("_id", "No id")
            meeting_link = item.get("url", "No Meeting Link")
            date = item.get("date", "No date")
            interview_time = item.get("time", "No time")

            if date != "No date" and interview_time != "No time":
                datetime_str = f"{date} {interview_time}"
                print(f"Processing interview scheduled at {datetime_str}")
                try:
                    interview_datetime_obj = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")
                    current_datetime = datetime.datetime.now()
                    print("Scheduled interview time:", interview_datetime_obj)
                    print("Current time:", current_datetime)

                    if current_datetime >= interview_datetime_obj - datetime.timedelta(minutes=1) and current_datetime <= interview_datetime_obj:
                        print("It's time to join the meeting:", meeting_link)
                        login(meeting_link, date, interview_id, title, names)
                    else:
                        print("Not the time to join the meeting yet.")
                except ValueError as e:
                    print(f"Error parsing date and time: {e}")
            else:
                print("Date or time is empty, cannot proceed.")

if __name__ == "__main__":
    main()

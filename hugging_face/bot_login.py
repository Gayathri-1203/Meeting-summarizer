import pyautogui
import time
from interview_record import Interview
import pygetwindow as gw
from Mapping_speakers import speaker_segments,process_conversation_file, create_pdf
import os
from read_mail import get_interview_data
from Diarization import transcribe_audio_files
from paddleocr import PaddleOCR
from Transcription import generate_summary,read_file, send_reply_to_participants,fetch_participant_emails,format_html_template,final
from Extract_speakers import extract_names_with_timestamps
import threading
import sys
import json

STOP = False
SAVE_FOLDER = "screenshots"

def ss():
    global STOP
    print("----------------------", time.time())
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    counter = 1
    while not STOP:
        for i in range(60):
            timestamp = f"{counter}sec"
            pyautogui.screenshot(os.path.join(SAVE_FOLDER, f"screenshot_{timestamp}.png"))
            time.sleep(1)
            counter += 1
        STOP = True

ocr = PaddleOCR()

def extract_text(image_path):
    res = ocr.ocr(image_path)
    return res[0]


def click_position(coordinates):
    """
    Clicks the position specified by the average of coordinates in the input list.
    Args:
    - coordinates (list): A list of coordinate pairs, where each pair is a list containing x and y coordinates.
    Returns:
    None
    """
    x_sum = sum(coord[0] for coord in coordinates)
    y_sum = sum(coord[1] for coord in coordinates)
    x_avg = x_sum / len(coordinates)
    y_avg = y_sum / len(coordinates)
    pyautogui.click(x_avg, y_avg)
    time.sleep(0.2)
    active_window = pyautogui.getActiveWindow()
    active_window.maximize()

class GoogleMeetHandler:
    def __init__(self, meet_url) -> None:
        print("#" * 100)
        self.meet_url = meet_url
        self.joined_meet = False
        self.has_candidates = False

    def handle_meet(self):
        self.join_meet()
        self.handle_popups()

    def join_meet(self):
        pyautogui.write(self.meet_url)
        pyautogui.press("enter")
        pyautogui.screenshot("joining_meet.png")
        time.sleep(2)

    def handle_popups(self):
        count = 0
        while not self.joined_meet:
            print("*" * 10, "  Handling PoUPS     ", "*" * 20)
            pyautogui.screenshot(f"meet_{count}.png")
            time.sleep(1)
            res = extract_text(f"meet_{count}.png")
            count += 1
            data = {each[-1][0]: each[0] for each in res}
            print(data)
            if "Allow microphone and camera" in data:
                print("Loaded the Meet  check for config popups")
                click_position(data["Allow microphone and camera"])
                self.allow_mic_and_camera()
            elif "Ready to join?" in data:
                print("Yes I am ready to join -------------------")
                for each in data:
                    if "join now" in each.lower():
                        # Turn off the camera and microphone before joining
                        pyautogui.hotkey("ctrl", "e")  # This typically turns off the camera in Google Meet
                        pyautogui.hotkey("ctrl", "d")  # This typically turns off the microphone in Google Meet
                        click_position(data[each])
                        self.joined_meet = True
                        break
            else:
                time.sleep(1)

        thread = threading.Thread(target=ss)
        thread.start()


class NewProfileCreator:
    def __init__(self) -> None:
        self.enter_email_screen = None
        self.enter_password_screen = None
        self.entered_password = False

    def navigate_to_signin(self):
        time.sleep(1)
        pyautogui.screenshot("newSignin.png")
        res = extract_text("newSignin.png")
        for each in res:
            if each[-1][0].strip().lower() == "sign in":
                print(each)
                print("clicking to sigin -------", each[0])
                click_position(each[0])
                time.sleep(1)
                self.enter_email()
        return

    def enter_email(self):
        for i in range(10):
            enter_email_coords = {}
            time.sleep(0.5)
            pyautogui.screenshot("enterEmail.png")
            res = extract_text("enterEmail.png")
            enter_email_coords = {each[-1][0]: each[0] for each in res}
            print(enter_email_coords)
            if any(
                each in ["Emailorphone", "Email or phone"]
                for each in enter_email_coords
            ):
                print("----------------yes-------------")

                email_coords = enter_email_coords.get("Emailorphone")
                if not email_coords:
                    email_coords = enter_email_coords.get("Email or phone")
                click_position(email_coords)
                time.sleep(0.2)
                pyautogui.typewrite("bdagra@walkingtree.tech")
                print("Entered the email--------")
                time.sleep(2)
                click_position(enter_email_coords["Next"])
                print("cliecked to enter the password--------")

                while not self.entered_password:
                    pyautogui.screenshot("enteredEmail.png")
                    time.sleep(0.1)
                    self.enter_password_screen = pyautogui.screenshot(
                        f"enter_password.png"
                    )
                    res = extract_text(f"enter_password.png")
                    data = {each[-1][0]: each[0] for each in res}
                    for field in res:
                        print(field)
                        if field[-1][0] == "Enteryourpassword":
                            print("f------------------", field)
                            click_position(field[0])
                            pyautogui.typewrite("Walking@0022")
                            self.entered_password = True
                            self.pass_coords = data
                            break
                        if field[-1][0] == "Enter your password":
                            print("f------------------", field)
                            click_position(field[0])
                            pyautogui.typewrite("Walking@0022")
                            self.entered_password = True
                            self.pass_coords = data
                            break
                        if field[-1][0] == "Show password":
                            pyautogui.press("tab")
                            continue

                click_position(self.pass_coords["Next"])
                return self.new_profile_config()

    def new_profile_config(self):
        time.sleep(1)
        while True:
            print("*" * 100)
            pyautogui.screenshot("config_1.png")
            res = extract_text("config_1.png")
            data = {each[-1][0]: each[0] for each in res}
            if "Welcome to your new profile" in data:
                print("#" * 20)
                click_position(data["Next"])
                break
        found_yes = False
        while not found_yes:
            pyautogui.screenshot("imin.png")
            res = extract_text("imin.png")
            data = {each[-1][0]: each[0] for each in res}
            if "Turn on sync" in data:
                print(data)
                print("on the trun on sync page")
                for each in data:
                    if "yes" in each.lower():
                        click_position(data[each])
                        found_yes = True
        while True:
            pyautogui.screenshot("profile_config.png")
            res = extract_text("profile_config.png")
            data = {each[-1][0]: each[0] for each in res}
            print(data)
            if "Customize your Chrome profile" in data:
                print(data)
                click_position(data["Done"])
                break

        print("Join the meeting")

    def click_position(self, coordinates):
        print("clicking to enter profile     ---", coordinates)
        # Calculate the average of x and y coordinates
        x_sum = sum(coord[0] for coord in coordinates)
        y_sum = sum(coord[1] for coord in coordinates)
        x_avg = x_sum / len(coordinates)
        y_avg = y_sum / len(coordinates)
        pyautogui.click(x_avg, y_avg)
        time.sleep(0.2)


class WindowDetector:
    def __init__(self, meeting_link) -> None:
        self.meet_url=meeting_link

    def googleProfile(self):
        """Whos is usig Chrome"""
        pyautogui.hotkey("win", "r")
        time.sleep(1)
        pyautogui.write("chrome")
        time.sleep(1)
        pyautogui.press("enter")
        while True:
            win = pyautogui.getActiveWindow()
            if win:
                if win.title == "Google Chrome":
                    win.maximize()
                    time.sleep(0.2)
                    pyautogui.screenshot("google_profiles.png")
                    if self.validate_window("google_profiles.png", "Who's using Chrome?"):
                        if self.validate_window("google_profiles.png", "Add"):
                            break
        time.sleep(1)
        res = extract_text("google_profiles.png")
        checked = self.check_profile(res, "BDA Agra")
        if checked:
            print("profile found", self.profile_coords)
            click_position(self.profile_coords)
        else:
            print("profile not found add profile coords  ", self.add_profile_coords)
            click_position(self.add_profile_coords)
            print("clicked on add profile ")
            time.sleep(2)
            pyautogui.screenshot("addedprofilebtn.png")

            ne = NewProfileCreator()
            ne.navigate_to_signin()

        for i in range(3):
            pyautogui.screenshot("profile_config.png")
            res = extract_text("profile_config.png")
            data = {each[-1][0]: each[0] for each in res}
            print(data)
            if "Enhanced ad privacy in Chrome" in data:
                print(data)
                click_position(data["Got it"])
                break

        me = GoogleMeetHandler(self.meet_url)
        print("--------------------------------------------in googe meet------------------------------")
        me.handle_meet()
        print("--------------------------------------------handled googe meet------------------------------")

        if me.joined_meet:
            print("Start the Interview")
            
            return {"started":True}
        else:
            return {"started":False}

    def check_profile(self, ocr_coords, profile_name):
        google_profiles_coords = {each[-1][0]: each[0] for each in ocr_coords}
        if "Add" in google_profiles_coords:
            print("&"*100)
            self.add_profile_coords = google_profiles_coords["Add"]
        else:
            return False
        if profile_name in google_profiles_coords:
            print("profile found at ", google_profiles_coords[profile_name])
            self.profile_found = True
            self.profile_coords = google_profiles_coords[profile_name]
            return True
        return False

    def validate_window(self, image_path, string):
        res = extract_text(image_path)
        for each in res:
            print(each[-1][0])
            if each[-1][0] == string:
                print("Yes on the profiles page---")
                return True
        return False

    def AddProfile(self):
        """Set up your new chrome profile"""
        while True:
            win = pyautogui.getActiveWindow()
            if win.title == "Google Chrome":
                win.maximize()
                time.sleep(2)
                pyautogui.screenshot("google_profiles.png")
                if self.validate_window("google_profiles.png", "Who's using Chrome?"):
                    break
            else:
                break
        time.sleep(1)


class WindowActionsPerformer:
    def welcome_to_new_profile(self, data):
        try:
            click_position(data["Next"])
            time.sleep(1)
            return True
        except Exception as e:
            print("Error in Welcome to new Profile ", e)
            return False

    def turn_on_sync(self, data):
        try:
            for each in data:
                if "yes" in each.lower():
                    click_position(data[each])
                    time.sleep(1)
                    return True
        except Exception as e:
            print("Error in Welcome to new Profile ", e)
            return False

    def customize_your_chrome_profile(Self, data):
        try:
            click_position(data["Done"])
            time.sleep(1)
            return True
        except Exception as e:
            print("Error in Welcome to new Profile ", e)
            return False

    def enhanced_ad_privacy_in_chrome(self, data):
        try:
            click_position(data["Got it"])
            time.sleep(1)
            return True
        except Exception as e:
            print("Error in Welcome to new Profile ", e)
            return False


files = os.listdir()

for file in files:
    if file.endswith(".png"):
        os.remove(file)

def login(meeting_link, date, interview_id, title, names):
    wd = WindowDetector(meeting_link)
    meet_id = meeting_link.split("/")[-1].split("?")[0]
    print(meet_id)
    print(f"Interview ID: {interview_id}")
    print(f"Interview Date: {date}")
    print(f"title : {title}")
    print(f"names: {names}")

    res = wd.googleProfile()
    if res["started"]:
        has_candidates = res.get("candidates")
        windows = pyautogui.getAllWindows()
        print(windows)
        is_candidate_present = False
        
        for window in windows:
            print(window.title)
            if meet_id in window.title.lower():
                print("Started the meeting.")
                print("Invoking the interview.")
                time.sleep(2)

                if has_candidates:
                    pyautogui.screenshot("checkcandidate.png")
                    res = extract_text("checkcandidate.png")
                    for each in res:
                        print(each)
                else:
                    print("-------------------start processing----------------")

                interview_instance = Interview()
                recorded_files = interview_instance.record_audio()
                print("-------------------------------recording completed-----------------")

                pyautogui.hotkey("ctrl", "w")
                print("Meeting window closed.")

                recordings_folder = "C:/Users/WakinkTree/Desktop/whisper/hugging_face/recorded_files"
                transcribe_audio_files(recordings_folder)
                print("------------------------transcribe_audio---------------------------")
                
                screenshots_folder = "C:/Users/WakinkTree/Desktop/whisper/hugging_face/screenshots"
                name_timestamp_map = extract_names_with_timestamps(screenshots_folder)

                output_file = "speaker_names.txt"
                with open(output_file, "w") as file:
                    json.dump(name_timestamp_map, file)
                print(f"Extracted names along with timestamps stored in {output_file}")
                print(name_timestamp_map)
                print("----------------------------------extracted speakers----------------------------")

                output_record_path = 'C:/Users/WakinkTree/Desktop/whisper/hugging_face/recorded_files/record_transcription.txt'
                names_timestamps_path = 'C:/Users/WakinkTree/Desktop/whisper/hugging_face/speaker_names.txt'
                updated_segments_path = 'C:/Users/WakinkTree/Desktop/whisper/hugging_face/segregate_speakers.txt'

                speaker_segments(output_record_path, names_timestamps_path, updated_segments_path)

                input_file = 'segregate_speakers.txt'
                conversations = process_conversation_file(input_file)
                create_pdf(conversations)
                print("PDF generated: conversation.pdf")

                final(title, date, names)




import time
import soundcard as sc
import soundfile as sf
import os
import speech_recognition as sr

class Interview:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def record_audio(self):
        SAMPLE_RATE = 48000
        RECORD_SEC = 60
        count = 0
        all_recordings = []
       
        output_dir = "recorded_files"
        os.makedirs(output_dir, exist_ok=True)

        while True:
            OUTPUT_FILE_NAME = os.path.join(output_dir, f"record.wav")
            try:
                with sc.default_microphone().recorder(samplerate=SAMPLE_RATE) as mic:
                    data = mic.record(numframes=SAMPLE_RATE * RECORD_SEC)
                sf.write(file=OUTPUT_FILE_NAME, data=data, samplerate=SAMPLE_RATE)
                all_recordings.append(OUTPUT_FILE_NAME)
            except Exception as e:
                print("Issue with microphone recording:", e)
                break
            print(f"Recording completed.")
            count += 1
            time.sleep(RECORD_SEC)
            
            if count >= 1:
                break
        
        return all_recordings


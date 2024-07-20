import os
import cv2
from paddleocr import PaddleOCR
import json

def extract_names_with_timestamps(screenshots_folder):
    lower_blue = (100, 50, 50)
    upper_blue = (140, 255, 255)

    ocr = PaddleOCR()

    name_timestamp_map = {}

    current_time = 1
    for filename in os.listdir(screenshots_folder):
        if filename.endswith(".png"):
            image_path = os.path.join(screenshots_folder, filename)
            timestamp = f"{current_time}sec"

            image = cv2.imread(image_path)
            if image is None:
                print(f"Failed to read image: {image_path}")
                continue

            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            mask = cv2.inRange(hsv_image, lower_blue, upper_blue)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            highlighted_text = ""

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                highlighted_roi = image[y:y+h, x:x+w]

                result = ocr.ocr(highlighted_roi)

                for line in result:
                    if isinstance(line, list):
                        for word in line:
                            highlighted_text += word[1][0] + " "
                    elif isinstance(line, dict):
                        for word_data in line.values():
                            if isinstance(word_data, list):
                                for word in word_data:
                                    if isinstance(word, list) and len(word) >= 2:
                                        highlighted_text += word[1] + " "

            highlighted_text = highlighted_text.strip()

            if highlighted_text:
                name_timestamp_map[timestamp] = highlighted_text

            current_time += 1
            if "import cv2" in highlighted_text:
                break

    return name_timestamp_map


# screenshots_folder = "C:/Users/WakinkTree/Desktop/whisper/hugging_face/screenshots"
# name_timestamp_map = extract_names_with_timestamps(screenshots_folder)
# output_file = "speaker_names.txt"
# with open(output_file, "w") as file:
#     json.dump(name_timestamp_map, file)

# print(f"Extracted names along with timestamps stored in {output_file}")
# print(name_timestamp_map)

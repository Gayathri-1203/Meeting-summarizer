import re
from fpdf import FPDF
import textwrap
from collections import defaultdict

def speaker_segments(output_record_path, names_timestamps_path, output_file_path):
    """
    Update speaker segments with names from a timestamp mapping and save to a file.

    :param output_record_path: Path to the output_record.txt file
    :param names_timestamps_path: Path to the names_timestamps.txt file
    :param output_file_path: Path to the file where updated segments will be stored
    :return: List of updated speaker segments
    """

    with open(output_record_path, 'r', encoding='utf-8') as file:
        first_output = file.read()

    with open(names_timestamps_path, 'r', encoding='utf-8') as file:
        second_output = file.read()

    name_timestamps = {}
    for match in re.finditer(r'"(\d+)sec": "([^"]+)"', second_output):
        timestamp = float(match.group(1))
        name = match.group(2)
        name_timestamps[timestamp] = name

    updated_speaker_segments = []

    for match in re.finditer(r'Speaker: (\w+), Start: ([\d.]+), End: ([\d.]+),\n Text: (.+)', first_output):
        speaker = match.group(1)
        start_time = float(match.group(2))
        end_time = float(match.group(3))
        text = match.group(4)

        name = speaker
        for timestamp, candidate_name in name_timestamps.items():
            if start_time <= timestamp <= end_time:
                name = candidate_name
                break

        updated_speaker_segments.append(f"Speaker: {name}, Start: {start_time}, End: {end_time},\n Text: {text}")

    with open(output_file_path, 'w', encoding='utf-8') as file:
        for segment in updated_speaker_segments:
            file.write(segment + "\n")

    return updated_speaker_segments

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=10)
        self.add_page()
        self.set_font("Arial", size=8)
        self.line_height = 4
        self.speaker_colors = {}
        self.color_palette = [(200, 200, 255), (255, 200, 200), (200, 255, 200), (255, 255, 200)]
        self.color_index = 0

    def get_speaker_color(self, speaker):
        if speaker not in self.speaker_colors:
            self.speaker_colors[speaker] = self.color_palette[self.color_index % len(self.color_palette)]
            self.color_index += 1
        return self.speaker_colors[speaker]

    def draw_circle(self, x, y, r, color):
        self.set_fill_color(*color)
        self.ellipse(x - r, y - r, 2 * r, 2 * r, 'F')

    def add_message(self, initials, name, timestamp, message):
        y_position = self.get_y()
        speaker_color = self.get_speaker_color(name)

        circle_x = 13
        circle_y = y_position + 2
        self.draw_circle(circle_x, circle_y, 3, speaker_color)
        self.set_xy(circle_x - 3, y_position)
        self.set_font("Arial", 'B', 6)
        self.set_text_color(0, 0, 0)
        self.cell(6, 4, initials, 0, 0, 'C')

        self.set_xy(17, y_position)
        self.set_font("Arial", '', 8)
        name_width = self.get_string_width(name)
        self.cell(name_width, 4, name, ln=False)

        self.set_xy(17 + name_width + 2, y_position)
        self.set_font("Arial", '', 4.5)  
        timestamp_with_s = timestamp + 's'
        timestamp_width = self.get_string_width(timestamp_with_s)
        self.cell(timestamp_width, 4, timestamp_with_s)

        self.ln(self.line_height + 1)

        self.set_xy(17, self.get_y())
        self.set_font("Arial", '', 6)
        wrapped_text = textwrap.wrap(message, width=95)
        for line in wrapped_text:
            self.multi_cell(0, 2.5, line)

        self.ln(self.line_height)

def process_conversation_file(input_file):
    conversations = []

    with open(input_file, 'r') as file:
        lines = file.readlines()

    current_speaker = None
    current_message = ""
    current_time = ""

    for line in lines:
        line = line.strip()
        if line.startswith("Speaker:"):
            if current_speaker is not None:
                conversations.append({
                    "name": current_speaker,
                    "time": current_time,
                    "message": current_message.strip()
                })
                current_message = ""
            
            current_speaker = line.split(",")[0].split(": ")[1].strip()
            current_time = line.split(",")[1].split(": ")[1].strip()

        elif line.startswith("Text:"):
            text = line.split(": ")[1].strip()
            current_message += text + "\n"

    if current_speaker is not None:
        conversations.append({
            "name": current_speaker,
            "time": current_time,
            "message": current_message.strip()
        })

    return conversations

def create_pdf(conversations):
    pdf = PDF()
    for item in conversations:
        initials = ''.join([name[0].upper() for name in item['name'].split() if name])
        pdf.add_message(initials, item['name'], item['time'], item['message'])
    pdf.output("conversation.pdf")

# input_file = 'segregate_speakers.txt'
# conversations = process_conversation_file(input_file)
# create_pdf(conversations)
# print("PDF generated: conversation.pdf")


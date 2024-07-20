import os
import json
from pymongo import MongoClient
from groq import Groq
from read_mail import send_reply_to_participants
from http.server import HTTPServer, SimpleHTTPRequestHandler

os.environ['GROQ_API_KEY'] = 'API_KEY'
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MONGODB_URI = 'URI'
DB_NAME = 'meetings'
COLLECTION_NAME = 'meeting_details'

def generate_summary(conversation):
    try:
        prompt = f"Given the following conversation:\n\n{conversation}\n\n"
        prompt += """Please analyze the conversation and provide the following information in JSON format:
                    {
                        "summary": "A summary of the conversation.",
                        "keypoints": ["Key point 1", "Key point 2", ...],
                        "actionitems": ["Action item 1", "Action item 2", ...],
                        "importantquestions": ["Question 1", "Question 2", ...]
                    }"""
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None

def read_file(filename):
    with open(filename, "r") as f:
        return f.read().strip()

def format_html_template(summary_data, title, date, names):
    key_points = ''.join([f'<li>{point}</li>' for point in summary_data['keypoints']])
    action_items = ''.join([f'<li>{item}</li>' for item in summary_data['actionitems']])
    guests = ''.join([f'<div class="guest"><span>{name}</span></div>' for name in names])
    
    STYLES = """<style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 20px;
      background-color: #f0f4f8;
    }
    h1 {
      font-size: 2em;
      margin: 0 0 10px;
    }
    .date {
      font-size: 1em;
      color: #888;
      margin: 0 0 20px;
    }
    .section {
      margin-bottom: 20px;
    }
    .section h3 {
      font-size: 1.5em;
      margin: 0 0 10px;
    }
    .section p {
      font-size: 1em;
      margin: 0 0 10px;
    }
    .section ul {
      margin: 0;
      padding-left: 20px;
      list-style-type: disc;
    }
    .section li {
      margin-bottom: 5px;
      font-size: 1em;
    }
    .guests {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 20px;
    }
    .guest {
      display: flex;
      align-items: center;
      background-color: #fff;
      padding: 5px 10px;
      border-radius: 5px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    </style>"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>{title}</title>
      {STYLES}
    </head>
    <body>
      <p class="date">{date}</p>
      <h1>{title}</h1>
      
      <div class="guests">
        {guests}
      </div>
      
      <div class="section">
        <h3>Summary</h3>
        <p>{summary_data['summary']}</p>
      </div>

      <div class="section">
        <h3>Key Points</h3>
        <ul>{key_points}</ul>
      </div>

      <div class="section">
        <h3>Action Items</h3>
        <ul>{action_items}</ul>
      </div>

    </body>
    </html>"""

    return html_content


def fetch_participant_emails():
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    participants = []
    
    for meeting in collection.find():
        participants.extend(meeting['names_emails'])
    
    client.close()
    return participants

def final(title, date, names):
    conversation_text = read_file("segregate_speakers.txt")
    summary_json = generate_summary(conversation_text)
    
    if summary_json:
        summary_data = json.loads(summary_json)
        
        html_summary = format_html_template(summary_data, title, date, names)
        
        participants = fetch_participant_emails()
        
        pdf_path = "conversation.pdf"
        send_reply_to_participants(html_summary, participants, pdf_path=pdf_path)
    else:
        print("No summary generated")


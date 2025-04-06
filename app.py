import os
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# LINE credentials from environment
LINE_CHANNEL_ACCESS_TOKEN = 's4bmQZyQi8JWJHKaLpofp7YiqtBOzjjDkekdDDBMxmFZ18TjR0FicGtjNzGQxKNK9E6iQdxZEOcVkWVYtNDKg0Bykz8ycC/i3NZeoAI/4ngQYaqsAnKKLOoUg6JL/AP++Jj7ko8zBqaWmWpvy0qkYgdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'f24a0d6a0e67b20306882e2cda6e1a04'
GOOGLE_SHEET_ID = '18XEwalClnj1dgjaG0ujT_0duhWe5NMzyNQ7Qg-9DiJE'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

# Questions (can be expanded to full 20)
questions = [
    {
        "text": "ข้อ 1: คุณชอบทำงานกับคนอื่นหรือคนเดียว?",
        "choices": {
            "A": {"text": "กับคนอื่น", "score": "E+2"},
            "B": {"text": "คนเดียว", "score": "I+2"},
            "C": {"text": "เฉยๆ", "score": "I+1"},
            "D": {"text": "คุยได้บ้าง", "score": "E+1"},
            "E": {"text": "แล้วแต่สถานการณ์", "score": "I+0"},
        }
    },
    {
        "text": "ข้อ 2: คุณตัดสินใจจากความรู้สึกหรือเหตุผล?",
        "choices": {
            "A": {"text": "ใช้เหตุผล", "score": "T+2"},
            "B": {"text": "ใช้ความรู้สึก", "score": "F+2"},
            "C": {"text": "ผสมกัน", "score": "T+1"},
            "D": {"text": "แล้วแต่เรื่อง", "score": "F+1"},
            "E": {"text": "ไม่แน่ใจ", "score": "F+0"},
        }
    },
    # เพิ่มคำถามจนถึงข้อ 20
]

# User session store
user_sessions = {}

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text.strip()

    if message_text.lower() == "เริ่มทำแบบทดสอบ":
        user_sessions[user_id] = {"answers": [], "current_question": 0}
        send_question(user_id, event.reply_token)
    elif user_id in user_sessions:
        session = user_sessions[user_id]
        session["answers"].append(message_text.upper())
        session["current_question"] += 1

        if session["current_question"] < len(questions):
            send_question(user_id, event.reply_token)
        else:
            mbti_result = calculate_mbti(session["answers"])
            faculties = recommend_faculties(mbti_result)
            save_to_google_sheet(user_id, session["answers"], mbti_result, faculties)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"คุณคือ {mbti_result}\nแนะนำคณะ: {', '.join(faculties)}")
            )
            del user_sessions[user_id]
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="พิมพ์ 'เริ่มทำแบบทดสอบ' เพื่อเริ่มทำแบบทดสอบ MBTI")
        )

def send_question(user_id, reply_token):
    session = user_sessions[user_id]
    q = questions[session["current_question"]]
    text = q["text"] + "\n" + "\n".join([f"{k}. {v['text']}" for k, v in q["choices"].items()])
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

def calculate_mbti(answers):
    scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}

    for i, ans in enumerate(answers):
        if i >= len(questions):
            continue
        q = questions[i]
        choice = q["choices"].get(ans.upper())
        if choice:
            trait, value = choice["score"][0], int(choice["score"][2])
            scores[trait] += value

    mbti = ""
    mbti += "E" if scores["E"] >= scores["I"] else "I"
    mbti += "S" if scores["S"] >= scores["N"] else "N"
    mbti += "T" if scores["T"] >= scores["F"] else "F"
    mbti += "J" if scores["J"] >= scores["P"] else "P"

    return mbti

def recommend_faculties(mbti_type):
    recommendations = {
        "INFP": ["มนุษยศาสตร์", "จิตวิทยา", "นิเทศศาสตร์"],
        # เพิ่ม MBTI อื่นๆ ตามความเหมาะสม
    }
    return recommendations.get(mbti_type, ["ไม่มีคำแนะนำคณะสำหรับ MBTI นี้"])

def save_to_google_sheet(user_id, answers, mbti_result, faculties):
    timestamp = datetime.now().isoformat()
    row = [timestamp, user_id] + answers + [mbti_result, ', '.join(faculties)]
    sheet.append_row(row)

if __name__ == "__main__":
    app.run(debug=True)

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
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials/credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

# Questions (can be expanded to full 20)
questions = [
    "ข้อ 1: คุณชอบทำงานกับคนอื่นหรือคนเดียว?\nA. กับคนอื่น\nB. คนเดียว",
    "ข้อ 2: คุณมักตัดสินใจโดยใช้เหตุผลหรือความรู้สึก?\nA. เหตุผล\nB. ความรู้สึก",
    # เพิ่มคำถามอีกจนถึงข้อ 20 ตามต้องการ
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
        send_question(user_id)
    elif user_id in user_sessions:
        session = user_sessions[user_id]
        session["answers"].append(message_text)
        session["current_question"] += 1

        if session["current_question"] < len(questions):
            send_question(user_id)
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

def send_question(user_id):
    session = user_sessions[user_id]
    question = questions[session["current_question"]]
    line_bot_api.push_message(user_id, TextSendMessage(text=question))

def calculate_mbti(answers):
    # ปรับตรรกะให้ตรงกับการคิดคะแนนจริงของคุณ
    return "INFP"  # placeholder

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

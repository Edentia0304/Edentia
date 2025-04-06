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
        "text": "ข้อ 1: หากคุณต้องไปเข้าค่ายร่วมกับเพื่อนจากต่างโรงเรียนและไม่มีเพื่อนจากโรงเรียนเดียวกันไปด้วยเลย คุณจะปฏิบัติตัวอย่างไร?",
        "choices": {
            "A": {"text": "เริ่มต้นแนะนำตนเองและทำความรู้จักกับเพื่อนต่างโรงเรียนทันที ", "score": "E+2"},
            "B": {"text": "ไม่ทำความรู้จักกับใครเลย เฝ้ารอวันจบค่าย ", "score": "I+2"},
            "C": {"text": "อยู่เฉย ๆ ใครเข้ามาก็คุยด้วย ไม่ได้ถือตัวอะไร", "score": "I+1"},
            "D": {"text": "สนุกกับกิจกรรมเต็มที่ ทำความรู้จักกับเพื่อนที่ต้องร่วมงานกัน", "score": "E+1"},
            "E": {"text": "ทำกิจกรรมตามที่ค่ายกำหนด รู้จักกับคนที่จำเป็นต้องรู้จักก็พอ", "score": "I+0"},
        }
    },
    {
        "text": "ข้อ 2: หากคุณจำเป็นต้องทำงานกลุ่มกับเพื่อนที่ไม่สนิท คุณคิดว่าตัวเองอยู่ตำแหน่งไหนของกลุ่ม?",
        "choices": {
            "A": {"text": "เป็นผู้สานสัมพันธ์ เวลาต้องการความช่วยเหลือจากเพื่อนกลุ่มอื่น ๆ", "score": "E+2"},
            "B": {"text": "เป็นผู้ตามที่ดี ทำหน้าที่ที่ได้รับมอบหมายก็พอ", "score": "I+2"},
            "C": {"text": "เป็นผู้เชื่อมโยง คอยออกความคิดเห็นและสอบถามความคิดเห็นเพื่อนในกลุ่ม", "score": "E+1"},
            "D": {"text": "เป็นผู้สังเกตการณ์ ให้ความร่วมมือเสมอ ออกความคิดเห็นบ้างถ้าถูกถาม", "score": "I+1"},
            "E": {"text": "เป็นผู้ยินดี หากไม่มีใครทำงานนี้ เดี๋ยวฉันทำให้ก็ได้", "score": "I+0"},
        }
    },
    {
        "text": "ข้อ 3: ในการเดินทางไปยังสถานที่ที่ไม่คุ้นเคย แล้วหลงกับเพื่อนและแบทโทรศัพท์หมด คุณจะทำอย่างไร?",
        "choices": {
            "A": {"text": "ขอยืมโทรศัพท์จากคนแปลกหน้าเพื่อติดต่อเพื่อนทันที", "score": "E+2"},
            "B": {"text": "ขอความช่วยเหลือจากเจ้าหน้าที่ที่จุดประชาสัมพันธ์", "score": "E+1"},
            "C": {"text": "เดินตามหาเพื่อนด้วยตนเองก่อน ถ้าไม่ไหวค่อยขอความช่วยเหลือ", "score": "I+1"},
            "D": {"text": "เลือกที่จะยืนรอเพื่อนที่จุดนัดพบ", "score": "I+1"},
            "E": {"text": "หาที่ชาร์จแบทโทรศัพท์ที่ใกล้ที่สุด", "score": "I+0"},
        }
    },
    {
        "text": "ข้อ 4: ในวันหยุดสุดสัปดาห์ คุณมักจะใช้เวลาส่วนใหญ่ไปกับอะไร?",
        "choices": {
            "A": {"text": "โทรชวนเพื่อนไปเที่ยวสักที่ และใช้ชีวิตสุดเหวี่ยงท่ามกลางผู้คน", "score": "E+2"},
            "B": {"text": "ทำกิจกรรมต่าง ๆ อยู่ห้อง เช่น นอน ดูซีรีย์ ดูการ์ตูน เล่นเกม", "score": "I+2"},
            "C": {"text": "ไม่ได้ทำอะไรเป็นพิเศษ แต่ถ้ามีเพื่อนชวนไปไหนก็ไปไม่ปฏิเสธเช่นกัน", "score": "I+0"},
            "D": {"text": "ออกไปตามห้าง ตลาด หรือที่ ๆ คิดว่ามีคนรู้จักไป เผื่อได้เที่ยวด้วยกัน", "score": "E+1"},
            "E": {"text": "ถามเพื่อนว่าจะไปเที่ยวด้วยกันหรือเปล่า ถ้าไม่ก็จะไปคนเดียว เพราะตั้งใจไว้อยู่แล้ว", "score": "I+0"},
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

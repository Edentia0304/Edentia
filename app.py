from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 's4bmQZyQi8JWJHKaLpofp7YiqtBOzjjDkekdDDBMxmFZ18TjR0FicGtjNzGQxKNK9E6iQdxZEOcVkWVYtNDKg0Bykz8ycC/i3NZeoAI/4ngQYaqsAnKKLOoUg6JL/AP++Jj7ko8zBqaWmWpvy0qkYgdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'f24a0d6a0e67b20306882e2cda6e1a04'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = f"คุณพิมพ์ว่า: {user_message}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def save_to_google_sheet(user_id, answers, mbti, scores, faculties):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/18XEwalClnj1dgjaG0ujT_0duhWe5NMzyNQ7Qg-9DiJE/edit?usp=sharing").sheet1

    row = [
        datetime.now().isoformat(),
        user_id,
        *answers,
        mbti,
        scores["E"], scores["I"],
        scores["S"], scores["N"],
        scores["T"], scores["F"],
        scores["J"], scores["P"],
        ", ".join(faculties)
    ]
    sheet.append_row(row)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

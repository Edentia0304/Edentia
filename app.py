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
questions_th = [
    {
        "text": "ข้อ 1: หากคุณต้องไปเข้าค่ายร่วมกับเพื่อนจากต่างโรงเรียนและไม่มีเพื่อนจากโรงเรียนเดียวกันไปด้วยเลย คุณจะปฏิบัติตัวอย่างไร?",
        "choices": {
            "A": {"text": "เริ่มต้นแนะนำตนเองและทำความรู้จักกับเพื่อนต่างโรงเรียนทันที ", "score": "E+2"},
            "B": {"text": "ไม่ทำความรู้จักกับใครเลย เฝ้ารอวันจบค่าย ", "score": "I+2"},
            "C": {"text": "อยู่เฉย ๆ ใครเข้ามาก็คุยด้วย ไม่ได้ถือตัวอะไร", "score": "I+1"},
            "D": {"text": "สนุกกับกิจกรรมเต็มที่ ทำความรู้จักกับเพื่อนที่ต้องร่วมงานกัน", "score": "E+1"},
            "E": {"text": "ทำกิจกรรมตามที่ค่ายกำหนด รู้จักกับคนที่จำเป็นต้องรู้จักก็พอ", "score": "I+1"},
        }
    },
    {
        "text": "ข้อ 2: หากคุณจำเป็นต้องทำงานกลุ่มกับเพื่อนที่ไม่สนิท คุณคิดว่าตัวเองอยู่ตำแหน่งไหนของกลุ่ม?",
        "choices": {
            "A": {"text": "เป็นผู้สานสัมพันธ์ เวลาต้องการความช่วยเหลือจากเพื่อนกลุ่มอื่น ๆ", "score": "E+2"},
            "B": {"text": "เป็นผู้ตามที่ดี ทำหน้าที่ที่ได้รับมอบหมายก็พอ", "score": "I+2"},
            "C": {"text": "เป็นผู้เชื่อมโยง คอยออกความคิดเห็นและสอบถามความคิดเห็นเพื่อนในกลุ่ม", "score": "E+1"},
            "D": {"text": "เป็นผู้สังเกตการณ์ ให้ความร่วมมือเสมอ ออกความคิดเห็นบ้างถ้าถูกถาม", "score": "I+1"},
            "E": {"text": "เป็นผู้ยินดี หากไม่มีใครทำงานนี้ เดี๋ยวฉันทำให้ก็ได้", "score": "E+1"},
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
            "C": {"text": "ไม่ได้ทำอะไรเป็นพิเศษ แต่ถ้ามีเพื่อนชวนไปไหนก็ไปไม่ปฏิเสธเช่นกัน", "score": "E+1"},
            "D": {"text": "ออกไปตามห้าง ตลาด หรือที่ ๆ คิดว่ามีคนรู้จักไป เผื่อได้เที่ยวด้วยกัน", "score": "E+1"},
            "E": {"text": "ถามเพื่อนว่าจะไปเที่ยวด้วยกันหรือเปล่า ถ้าไม่ก็จะไปคนเดียว เพราะตั้งใจไว้อยู่แล้ว", "score": "I+0"},
        }
    },
    {
    "text": "ข้อ 5: คุณคิดว่าเทศกาลใดที่ทำให้คุณรู้สึกมีความสุขมากที่สุด?",
    "choices": {
      "A": { "text": "คริสต์มาสสิ เตรียมเหมาสินค้าลดราคาในห้างและฉลองกับเพื่อน", "score": "E+1" },
      "B": { "text": "สงกรานต์สิ จะได้ออกไปเที่ยวกับเพื่อน เล่นน้ำ ปะแป้ง", "score": "E+2" },
      "C": { "text": "วาเลนไทน์สิ นาน ๆ ทีจะได้อยู่กับแฟนในคืนที่โรแมนติก", "score": "I+1" },
      "D": { "text": "ลอยกระทงสิ ซุ้มงานวัดสนุก ๆ กำลังรอเราอยู่", "score": "E+1" },
      "E": { "text": "ปีใหม่สิ หยุดยาวทั้งทีจะได้พักผ่อนข้ามปีหน่อย", "score": "I+2" }
        }
    },
    {
    "text": "ข้อ 6: ในบรรดาความสนใจของคุณ คุณคิดว่าตัวเองสนใจด้านใดมากที่สุด?",
    "choices": {
      "A": { "text": "การคำนวณ กฎเกณฑ์และทฤษฎีที่ตายตัว", "score": "S+2" },
      "B": { "text": "ทักษะทางภาษา ฟัง พูด อ่าน เขียน", "score": "S+1" },
      "C": { "text": "ค้นหาสิ่งใหม่ ๆ บนพื้นฐานของวิทยาศาสตร์", "score": "S+1" },
      "D": { "text": "งานศิลปะ ดนตรี ความสวยงาม ความสุนทรีย์", "score": "N+2" },
      "E": { "text": "วัฒนธรรม ประวัติศาสตร์ การดำรงอยู่ของสังคม", "score": "N+1" }
        }
    },
    {
    "text": "ข้อ 7: ในการอ่านนิยายสักเล่ม หรือดูหนังสักเรื่อง คุณมักมีกระบวนการคิดแบบใด?",
    "choices": {
      "A": { "text": "อินไปกับเนื้อหา และอารมณ์ที่ส่งออกมาถึงตนเอง", "score": "N+2" },
      "B": { "text": "วิจารณ์ตัวละคร ว่าถ้าเป็นฉันจะทำแบบนี้", "score": "N+1" },
      "C": { "text": "มีมุมมองเทียบกับโลกแห่งความเป็นจริง", "score": "S+1" },
      "D": { "text": "ขอดูสปอยล์ตอนจบก่อน ถ้าดีจะมาต่อให้จบ", "score": "N+1" },
      "E": { "text": "วิเคราะห์บท เนื้อหา และสิ่งที่ตัวละครต้องการสื่อให้เห็น", "score": "S+2" }
        }
    },
    {
    "text": "ข้อ 8: หากคุณจะซื้อสินค้าสักชิ้น คุณจะซื้อจากอะไร?",
    "choices": {
      "A": { "text": "รีวิวจากผู้ใช้จริง", "score": "S+2" },
      "B": { "text": "ศิลปินที่เราชอบเป็นพรีเซนเตอร์แบรนด์นี้", "score": "N+1" },
      "C": { "text": "เพื่อนแนะนำ", "score": "S+1" },
      "D": { "text": "ซื้อเพราะอยากซื้อ และซื้อเลย", "score": "N+2" },
      "E": { "text": "ส่วนผสมและผลลัพธ์ที่ได้", "score": "N+1" }
        }
    },
    {
    "text": "ข้อ 9: จากการ์ตูน Tom & Jerry คุณคิดว่าสัตว์สองชนิดนี้ไล่ล่ากันจริงหรือไม่?",
    "choices": {
      "A": { "text": "จริง มันเป็นธรรมชาติของแมวที่ต้องล่าหนูเพื่อเป็นอาหารอยู่แล้ว", "score": "S+2" },
      "B": { "text": "ฉันว่าไม่หรอก จริง ๆ สองตัวนี้รักกัน ทอมแกล้งล่าเพื่อไม่ให้เจ้านายด่า ส่วนเจอร์รี่แกล้งถูกล่าเพื่อที่จะได้อยู่ในบ้านเรื่อย ๆ", "score": "N+2" },
      "C": { "text": "มันก็แค่การ์ตูน จะไปใส่ใจอะไรมาก ผู้แต่งคงไม่มานั่งคิดขนาดนี้หรอก", "score": "S+1" },
      "D": { "text": "ความจริงไม่ว่าจะล่ากันหรือไม่ ฉันก็จะดูเพียงเพราะว่ามันสนุก", "score": "N+1" },
      "E": { "text": "ฉันไม่เคยนึกถึงเหตุผลที่ต้องมานั่งวิเคราะห์เรื่องนี้มาก่อน ว่าแต่มันล่ากันจริงหรือเปล่านะ", "score": "S+0" }
        }
    },
    {
    "text": "ข้อ 10: ถ้าคุณจะประดิษฐ์นวัตกรรมขึ้นมาชิ้นหนึ่งจากเรื่องโดเรม่อน คุณคิดว่าจะประดิษฐ์อะไร?",
    "choices": {
      "A": { "text": "ประตูไปที่ไหนก็ได้", "score": "S+2" },
      "B": { "text": "ไฟฉายย่อ/ขยายส่วน", "score": "N+1" },
      "C": { "text": "วุ้นแปลภาษา", "score": "S+1" },
      "D": { "text": "ผ้าคลุมกาลเวลา", "score": "N+2" },
      "E": { "text": "ไทม์แมชชีน", "score": "N+1" }
        }
    },
    {
    "text": "ข้อ 11: หากคุณเห็นเพื่อนของคุณทำผิดกฎ คุณจะจัดการอย่างไร?",
    "choices": {
      "A": { "text": "รวบรวมหลักฐาน แล้วนำไปแจ้งคุณครูทันที", "score": "T+2" },
      "B": { "text": "เข้าไปตักเตือนก่อน ถ้าไม่ฟังก็นำไปแจ้งคุณครู", "score": "T+1" },
      "C": { "text": "ทำเป็นไม่รู้ไม่เห็น แต่ก็รู้สึกผิดกับตนเอง", "score": "F+1" },
      "D": { "text": "เข้าไปพูดคุยถึงเหตุผลที่ต้องทำผิด จากนั้นหาทางออกที่ดีกว่า", "score": "F+1" },
      "E": { "text": "ช่วยดูต้นทางให้ เพราะยังไงก็เป็นเพื่อนของเรา", "score": "F+2" }
        }
    },
    {
    "text": "ข้อ 12: หากคุณมีปัญหากับแฟน แม้ปัญหาไม่ได้เกิดจากคุณเองก็ตาม แต่แฟนโวยวายใส่คุณไม่หยุด คุณจะ...",
    "choices": {
      "A": { "text": "บอกไปว่า อย่าทำแบบนี้ ปัญหาไม่ได้เกิดจากฉัน", "score": "T+2" },
      "B": { "text": "บอกไปว่า ไว้เราใจเย็นทั้งคู่ค่อยคุยกันไหม", "score": "T+1" },
      "C": { "text": "เลือกที่จะเงียบ รออีกฝ่ายใจเย็นแล้วค่อยคุย", "score": "T+1" },
      "D": { "text": "เป็นฝ่ายพูดขอโทษออกไปทันที แล้วปรับความเข้าใจ", "score": "F+1" },
      "E": { "text": "โวยวายกลับ เพราะปัญหาไม่ได้เกิดจากฉัน", "score": "F+2" }
        }
    },
    {
    "text": "ข้อ 13: เวลาคุณเล่นเกมแล้วแพ้บ่อยจนทำให้ตัวเองรู้สึกโมโห คุณมีวิธีการจัดการกับอารมณ์นี้ของคุณอย่างไร?",
    "choices": {
      "A": { "text": "วิเคราะห์ว่าความโมโหของคุณเกิดจากอะไร โมโหไปแล้วได้อะไร", "score": "T+2" },
      "B": { "text": "พยายามหาวิธีคลายความโมโหของตัวเองให้เร็วที่สุด เช่น ดูหนัง ฟังเพลง", "score": "T+1" },
      "C": { "text": "กดความอารมณ์ไว้ แม้ว่าจะยังไม่หายดี แต่เราต้องไม่แสดงออก", "score": "F+1" },
      "D": { "text": "แสดงออกทางสีหน้าชัดเจน ไม่ว่าใครก็อย่ามายุ่งกับฉัน", "score": "F+1" },
      "E": { "text": "ปลดปล่อยอารมณ์ด้วยการทำลายข้าวของ เช่น ปาโทรศัพท์", "score": "F+2" }
        }
    },
    {
    "text": "ข้อ 14: คุณคิดว่าเพลย์ลิสต์ในยูทูปแบบใดที่เข้ากับคุณมากที่สุด?",
    "choices": {
      "A": { "text": "ติวหนังสือ แนวข้อสอบสนามต่าง ๆ", "score": "T+2" },
      "B": { "text": "สารคดี อัตชีวประวัติบุคคลที่มีชื่อเสียง", "score": "T+1" },
      "C": { "text": "เทคนิคการใช้ชีวิต ไลฟ์โค้ช", "score": "T+0" },
      "D": { "text": "ASMR เสียงดนตรีที่ช่วยให้นอนหลับ", "score": "F+1" },
      "E": { "text": "เพลง ซีรี่ย์ คลิปตลก", "score": "F+2" }
        }
    },
    {
    "text": "ข้อ 15: ในการทำงานกลุ่ม มักจะมีปัญหาเกิดขึ้นบ่อยครั้งเพราะความคิดเห็นไม่ลงลอยกัน คุณจะเป็นบุคคลที่...",
    "choices": {
      "A": { "text": "เดินหนี เพราะปัญหานั้นไม่ได้ส่งผลดีต่อฉัน", "score": "T+1" },
      "B": { "text": "ไกล่เกลี่ย พยายามหาทางออกที่เป็นกลางที่สุด", "score": "F+2" },
      "C": { "text": "เลือกฝ่ายที่ถูกต้องด้วยเหตุผล แม้ว่าจะขัดใจอีกฝ่ายก็ตาม", "score": "T+2" },
      "D": { "text": "จัดการปัญหาด้วยการโหวต", "score": "T+1" },
      "E": { "text": "ร่วมวงปัญหา โดยการเสนอแนวคิดที่สาม", "score": "F+1" }
        }
    },
    {
    "text": "ข้อ 16: คุณเป็นคนที่เวลามีนัด คุณจะไปตอน...",
    "choices": {
      "A": { "text": "ก่อนเวลานัดราว ๆ 10 – 15 นาที", "score": "J+2" },
      "B": { "text": "ไปตรงเวลาอย่างกับจับวาง", "score": "J+1" },
      "C": { "text": "ตรงบ้างสายบ้างแล้วแต่จังหวะ", "score": "P+1" },
      "D": { "text": "นัดสิบโมงตื่นสิบโมง", "score": "P+1" },
      "E": { "text": "ไปตามเวลากะเทย", "score": "P+2" }
        }
    },
    {
    "text": "ข้อ 17: ทุกครั้งที่คุณกำลังทำงานหรือวางแผนงาน มักจะมีเหตุการณ์เหล่านี้เกิดขึ้นเสมอ?",
    "choices": {
      "A": { "text": "สามารถทำงานตามแผนที่วางไว้และเสร็จได้ตรงเวลา", "score": "J+2" },
      "B": { "text": "มีการปรับเปลี่ยนแผนงานเล็กน้อยแต่ยังได้ผลลัพธ์คงเดิม", "score": "J+1" },
      "C": { "text": "เร่งทำให้เสร็จตามเวลาแม้จะข้ามบางขั้นตอนไปบ้าง", "score": "J+1" },
      "D": { "text": "ไม่ค่อยทำตามแผนที่วางไว้สักเท่าไหร่ เพราะระหว่างทางเจอแผนที่ง่ายกว่า", "score": "P+1" },
      "E": { "text": "มีความคิดมากมายผุดขึ้นมา จนบางทีก็เปลี่ยนหัวข้อกะทันหัน", "score": "P+2" }
        }
    },
    {
    "text": "ข้อ 18: หากเปรียบเทียบคุณกับตำแหน่งหน้าที่ต่อไปนี้ คุณคิดว่าคุณเป็นใคร?",
    "choices": {
      "A": { "text": "นักวางแผน เพราะคุณชอบความแน่ชัด และทำงานได้อย่างเป็นระบบ", "score": "J+2" },
      "B": { "text": "เลขานุการ แม้คุณไม่ชอบออกความคิดเห็นเท่าไหร่ แต่คุณสามารถดำเนินการตามแผนได้อย่างดี", "score": "J+1" },
      "C": { "text": "ลูกทีม งานจะเสร็จช้าหรือเร็วก็ขึ้นอยู่กับหัวหน้างานนั่นแหละ", "score": "J+1" },
      "D": { "text": "นักปรับเปลี่ยน อาจไม่ลงลอยกับนักวางแผนเท่าไหร่ แต่วิธีการฉันมันยืดหยุ่นกว่านะ", "score": "P+1" },
      "E": { "text": "คนขี้เกียจ ทำไมทุกคนไม่ทำตัวสบาย ๆ ค่อย ๆ ทำ เดี๋ยวก็เสร็จเอง งานมันไม่ไปไหนหรอก", "score": "P+2" }
        }
    },
    {
    "text": "ข้อ 19: หากคุณมีนัดที่สำคัญมาก ๆ เช่น นัดเดตกับแฟนในวันครบรอบ เป็นต้น แต่เกิดการจราจรหนาแน่นสุด ๆ คุณจะทำอย่างไร?",
    "choices": {
      "A": { "text": "ไม่ได้ส่งผลกระทบอะไรต่อคุณมาก เพราะมีแผนสำรองเสมอ", "score": "J+2" },
      "B": { "text": "เปิด GPS วางแผนและตัดสินใจอย่างรวดเร็วเพื่อหาเส้นทางที่สามารถไปได้ตรงเวลาที่สุด", "score": "J+1" },
      "C": { "text": "เลือกเส้นทางเดิม แต่โทรแจ้งอีกฝ่ายให้ทราบล่วงหน้าว่าอาจไปสายเพื่อไม่ให้เกิดการเสียความรู้สึก", "score": "J+1" },
      "D": { "text": "คุณนั่งวิเคราะห์แนวทางที่สามารถทำได้ ณ ขณะนั้น เพราะไม่ได้เตรียมแผนสำรองมาล่วงหน้า", "score": "P+1" },
      "E": { "text": "คุณตัดสินใจทันทีโดยการขึ้นวินมอเตอร์ไซค์เพื่อไปให้ถึงที่หมายโดยไม่ได้วางแผนอะไรเลย", "score": "P+2" }
        }
    },
    {
    "text": "ข้อ 20: ในขณะที่คุณกำลังทำงานชิ้นหนึ่งอยู่ แต่เพื่อนสนิทของคุณชวนไปปาร์ตี้ คุณจะทำอย่างไร?",
    "choices": {
      "A": { "text": "ปฏิเสธทันทีเพราะคุณวางแผนเอาไว้แล้ว และไม่มีใครจะมาทำลายแผนงานของคุณได้", "score": "J+2" },
      "B": { "text": "ตอบตกลง แต่บอกเพื่อนว่าจะไปช้าหน่อย เพราะมีงานที่ต้องทำให้เสร็จ", "score": "J+1" },
      "C": { "text": "บอกเพื่อนว่าอาจจะไปหรือไม่ไปก็ได้ ขึ้นอยู่กับงานที่ทำอยู่ เดี๋ยวบอกอีกที", "score": "P+1" },
      "D": { "text": "เปลี่ยนแผนงานเกือบทั้งหมดเพื่อให้งานเสร็จทันเวลา จะได้รีบไปปาร์ตี้", "score": "P+1" },
      "E": { "text": "คุณเป็นคนมีความสามารถมากพอที่จะปาร์ตี้ไปด้วยและทำงานไปด้วยได้", "score": "P+2" }
        }
    }
    ]

questions_en = [
  {
    "text": "Question 1: If you go to a camp with students from other schools and no one from your school comes with you, what will you do?",
    "choices": {
      "A": { "text": "Start by introducing yourself and making new friends right away.", "score": "E+2" },
      "B": { "text": "Don’t talk to anyone and just wait for the camp to end.", "score": "I+2" },
      "C": { "text": "Stay quiet, but if someone talks to you, you talk back.", "score": "I+1" },
      "D": { "text": "Have fun with the activities and try to get to know friends you work with.", "score": "E+1" },
      "E": { "text": "Join the activities and only talk to people you need to know.", "score": "I+1" }
    }
  },
  {
    "text": "Question 2: If you must work in a group with people you don’t know well, what will be your role?",
    "choices": {
      "A": { "text": "Talk to other groups when your group needs help.", "score": "E+2" },
      "B": { "text": "Just follow and do the job you’re given.", "score": "I+2" },
      "C": { "text": "Share your ideas and ask others for their ideas.", "score": "E+1" },
      "D": { "text": "Listen and help, but only speak when someone asks.", "score": "I+1" },
      "E": { "text": "Say “It’s okay, I’ll do it” if no one wants to do something.", "score": "E+1" }
    }
  },
  {
    "text": "Question 3: You’re in a new place and get lost from your friends. Your phone battery is dead. What do you do?",
    "choices": {
      "A": { "text": "Ask a stranger to use their phone to call your friends.", "score": "E+2" },
      "B": { "text": "Ask for help from someone at the information counter.", "score": "E+1" },
      "C": { "text": "Try to find your friends by yourself first. If not, then ask for help.", "score": "I+1" },
      "D": { "text": "Wait at the meeting place for your friends.", "score": "I+1" },
      "E": { "text": "Look for a place to charge your phone.", "score": "I+0" }
    }
  },
  {
    "text": "Question 4: What do you usually do on weekends?",
    "choices": {
      "A": { "text": "Call friends to go out and have fun together.", "score": "E+2" },
      "B": { "text": "Stay in your room and do things like sleep, watch series or cartoons, play games.", "score": "I+2" },
      "C": { "text": "Don’t plan anything, but if friends ask you out, you’ll go.", "score": "E+1" },
      "D": { "text": "Go to a mall or market where you might see someone you know.", "score": "E+1" },
      "E": { "text": "Ask friends if they want to go out. If not, you still go alone as planned.", "score": "I+0" }
    }
  },
  {
    "text": "Question 5: Which festival makes you the happiest?",
    "choices": {
      "A": { "text": "Christmas – shopping and celebrating with friends.", "score": "E+1" },
      "B": { "text": "Songkran – go out, splash water, and have fun with friends.", "score": "E+2" },
      "C": { "text": "Valentine’s Day – a romantic night with your partner.", "score": "I+1" },
      "D": { "text": "Loy Krathong – fun at the fair with food and games.", "score": "E+1" },
      "E": { "text": "New Year – long holiday and time to relax.", "score": "I+2" }
    }
  },
  {
    "text": "Question 6: What are you most interested in?",
    "choices": {
      "A": { "text": "Math, rules, and clear answers.", "score": "S+2" },
      "B": { "text": "Language – listening, speaking, reading, and writing.", "score": "S+1" },
      "C": { "text": "Finding new things using science.", "score": "S+1" },
      "D": { "text": "Art, music, and beautiful things.", "score": "N+2" },
      "E": { "text": "Culture, history, and how people live.", "score": "N+1" }
    }
  },
  {
    "text": "Question 7: When you read a novel or watch a movie, what do you think about?",
    "choices": {
      "A": { "text": "Feel the story and the emotions deeply.", "score": "N+2" },
      "B": { "text": "Think what you would do if you were the character.", "score": "N+1" },
      "C": { "text": "Compare the story to real life.", "score": "S+1" },
      "D": { "text": "Check the ending first. If it’s good, then you continue.", "score": "N+1" },
      "E": { "text": "Try to understand the message the story wants to give.", "score": "S+2" }
    }
  },
  {
    "text": "Question 8: When you buy something, what affects your choice most?",
    "choices": {
      "A": { "text": "Real reviews from other people.", "score": "S+2" },
      "B": { "text": "Your favorite star is in the ad.", "score": "N+1" },
      "C": { "text": "Your friend tells you to buy it.", "score": "S+1" },
      "D": { "text": "You just feel like buying it.", "score": "N+2" },
      "E": { "text": "The ingredients and results.", "score": "N+1" }
    }
  },
  {
    "text": "Question 9: In Tom & Jerry, do you think cats and mice really chase each other?",
    "choices": {
      "A": { "text": "Yes, cats chase mice because it’s nature.", "score": "S+2" },
      "B": { "text": "No, they pretend to chase to help each other.", "score": "N+2" },
      "C": { "text": "It’s just a cartoon, don’t think too much.", "score": "S+1" },
      "D": { "text": "I watch it because it’s fun, not for the reason.", "score": "N+1" },
      "E": { "text": "I never really thought about it.", "score": "S+0" }
    }
  },
  {
    "text": "Question 10: If you could invent something from Doraemon, what would it be?",
    "choices": {
      "A": { "text": "Anywhere door.", "score": "S+2" },
      "B": { "text": "Shrink/grow flashlight.", "score": "N+1" },
      "C": { "text": "Translation jelly.", "score": "S+1" },
      "D": { "text": "Time cloth.", "score": "N+2" },
      "E": { "text": "Time machine.", "score": "N+1" }
    }
  },
  {
    "text": "Question 11: If you see your friend break the rules, what will you do?",
    "choices": {
      "A": { "text": "Collect proof and tell the teacher right away.", "score": "T+2" },
      "B": { "text": "Warn them first. If they don’t stop, then tell the teacher.", "score": "T+1" },
      "C": { "text": "Act like you didn’t see it, but feel bad inside.", "score": "F+1" },
      "D": { "text": "Talk to them and try to help find a better way.", "score": "F+1" },
      "E": { "text": "Help them because they’re your friend.", "score": "F+2" }
    }
  },
  {
    "text": "Question 12: If your partner gets angry at you even though it’s not your fault, what do you do?",
    "choices": {
      "A": { "text": "Tell them not to act like that—it’s not your fault.", "score": "T+2" },
      "B": { "text": "Say, 'Let’s talk when we both feel calm.'", "score": "T+1" },
      "C": { "text": "Stay quiet and wait for them to calm down.", "score": "T+1" },
      "D": { "text": "Say sorry first and then talk it out.", "score": "F+1" },
      "E": { "text": "Shout back because it’s not your fault.", "score": "F+2" }
    }
  },
  {
    "text": "Question 13: If you lose a game many times and get really angry, what do you do?",
    "choices": {
      "A": { "text": "Think about why you’re angry and what it helps.", "score": "T+2" },
      "B": { "text": "Try to calm down quickly, like watching a movie or listening to music.", "score": "T+1" },
      "C": { "text": "Hold the anger in and don’t show it.", "score": "F+1" },
      "D": { "text": "Show on your face that you're mad. Don’t talk to me.", "score": "F+1" },
      "E": { "text": "Break something like throwing your phone.", "score": "F+2" }
    }
  },
  {
    "text": "Question 14: What kind of YouTube playlist fits you best?",
    "choices": {
      "A": { "text": "Study tips and exam tricks.", "score": "T+2" },
      "B": { "text": "Documentaries and famous people’s stories.", "score": "T+1" },
      "C": { "text": "Life tips and coaching videos.", "score": "T+0" },
      "D": { "text": "ASMR and relaxing music.", "score": "F+1" },
      "E": { "text": "Music, series, and funny clips.", "score": "F+2" }
    }
  },
  {
    "text": "Question 15: When there are problems in group work because of different ideas, what do you do?",
    "choices": {
      "A": { "text": "Walk away because it’s not useful for you.", "score": "T+1" },
      "B": { "text": "Try to help solve it in a fair way.", "score": "F+2" },
      "C": { "text": "Pick the side that is right, even if someone gets upset.", "score": "T+2" },
      "D": { "text": "Suggest a vote to decide.", "score": "T+1" },
      "E": { "text": "Share a new idea to help both sides.", "score": "F+1" }
    }
  },
  {
    "text": "Question 16: When you have an appointment, you usually arrive...",
    "choices": {
      "A": { "text": "10–15 minutes early.", "score": "J+2" },
      "B": { "text": "Right on time.", "score": "J+1" },
      "C": { "text": "Sometimes on time, sometimes late.", "score": "P+1" },
      "D": { "text": "Wake up at the same time as the appointment.", "score": "P+1" },
      "E": { "text": "Come late with no rush.", "score": "P+2" }
    }
  },
  {
    "text": "Question 17: When working on a task or project, what often happens?",
    "choices": {
      "A": { "text": "You follow your plan and finish on time.", "score": "J+2" },
      "B": { "text": "You change the plan a bit but still finish well.", "score": "J+1" },
      "C": { "text": "You rush and may skip steps to finish on time.", "score": "J+1" },
      "D": { "text": "You don’t follow the plan because you find an easier way.", "score": "P+1" },
      "E": { "text": "You get many new ideas and sometimes change your topic.", "score": "P+2" }
    }
  },
  {
    "text": "Question 18: Which job fits you best?",
    "choices": {
      "A": { "text": "Planner – you like clear steps and working in order.", "score": "J+2" },
      "B": { "text": "Secretary – you don’t talk much but follow plans well.", "score": "J+1" },
      "C": { "text": "Team member – your work depends on the leader.", "score": "J+1" },
      "D": { "text": "Adapter – not always with the plan but more flexible.", "score": "P+1" },
      "E": { "text": "Lazy one – no rush, things will get done later.", "score": "P+2" }
    }
  },
  {
    "text": "Question 19: If you have an important date but there’s heavy traffic, what do you do?",
    "choices": {
      "A": { "text": "You’re fine because you always have a backup plan.", "score": "J+2" },
      "B": { "text": "Use GPS to find the fastest way.", "score": "J+1" },
      "C": { "text": "Take the same route but call ahead to explain.", "score": "J+1" },
      "D": { "text": "Think about what to do because you didn’t plan before.", "score": "P+1" },
      "E": { "text": "Quickly get on a motorbike without thinking much.", "score": "P+2" }
    }
  },
  {
    "text": "Question 20: You are working on something, but your best friend invites you to a party. What do you do?",
    "choices": {
      "A": { "text": "Say no right away because you already planned your work.", "score": "J+2" },
      "B": { "text": "Say yes but tell your friend you’ll come late.", "score": "J+1" },
      "C": { "text": "Say maybe. You’ll decide depending on your work.", "score": "P+1" },
      "D": { "text": "Change your work plan to finish fast and go.", "score": "P+1" },
      "E": { "text": "Party and work at the same time. You can do both.", "score": "P+2" }
    }    
  }
]

# User session store
user_sessions = {}    
def format_text_bar_chart(scores, title="ลักษณะบุคลิกภาพของคุณ"):
    chart_lines = [title]
    for trait in ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']:
        val = scores[trait]
        bar = "█" * val
        chart_lines.append(f"{trait}: {bar} ({val})")
    return "\n".join(chart_lines)
    
def calculate_mbti(answers, questions):
    scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    for i, ans in enumerate(answers):
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

    return mbti, scores    
@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400
    return 'OK', 200

import math
def reduce_ratio(a, b):
    if a == 0 and b == 0:
        return (0, 0)
    gcd = math.gcd(a, b)
    return (a // gcd, b // gcd)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text.strip()

    if message_text.lower() == "เริ่มทำแบบทดสอบ":
        user_sessions[user_id] = {"state": "waiting_language"}
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="กรุณาเลือกภาษา:\nพิมพ์ 'ไทย' หรือ 'English'")
        )
        return

    # ✅ ต้องเช็ก state ก่อน
    if user_sessions.get(user_id, {}).get("state") == "waiting_language":
        if message_text.lower() in ["thai", "ไทย", "english"]:
            lang = "th" if "thai" in message_text.lower() or "ไทย" in message_text.lower() else "en"
            user_sessions[user_id] = {
                "language": lang,
                "state": "doing_quiz",
                "answers": [],
                "current_question": 0
            }
            send_question(user_id, event.reply_token)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="กรุณาพิมพ์ 'ไทย' หรือ 'English' เท่านั้นครับ 😊")
            )
        return

    # ทำแบบทดสอบ
    elif user_id in user_sessions:
        session = user_sessions[user_id]
        lang = session.get("language", "th")
        questions = questions_th if lang == "th" else questions_en
        current_q = session["current_question"]

        if current_q >= len(questions):
            return  # กันพลาดถ้าเลย index

        q = questions[current_q]
        answer = message_text.upper()

        if answer not in q["choices"]:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="กรุณาตอบด้วย A, B, C, D หรือ E เท่านั้นค่ะ 😊\n\n" +
                         q["text"] + "\n" +
                         "\n".join([f"{k}. {v['text']}" for k, v in q["choices"].items()])
                )
            )
            return

        session["answers"].append(answer)
        session["current_question"] += 1

        if session["current_question"] < len(questions):
            send_question(user_id, event.reply_token)
        else:
            # ✅ ตรงนี้แหละ ที่ควรเรียก calculate_mbti
            mbti_result, scores = calculate_mbti(session["answers"], questions)

            info = get_mbti_info(mbti_result, lang)
            save_to_google_sheet(user_id, session["answers"], mbti_result, info["careers"])

            i, e = reduce_ratio(scores['I'], scores['E'])
            n, s = reduce_ratio(scores['N'], scores['S'])
            t, f = reduce_ratio(scores['T'], scores['F'])
            j, p = reduce_ratio(scores['J'], scores['P'])

            # ✅ เลือกคำตามภาษา
            if lang == "th":
                ratios = f"""อัตราส่วนลักษณะ:
I:E = {i}:{e}
N:S = {n}:{s}
T:F = {t}:{f}
J:P = {j}:{p}"""
                heading = "คุณคือ"
                meaning = "ความหมาย"
                careers = "อาชีพที่เหมาะสม"
                bar_title = "ลักษณะบุคลิกภาพของคุณ"
            else:
                ratios = f"""Trait Ratios:
I:E = {i}:{e}
N:S = {n}:{s}
T:F = {t}:{f}
J:P = {j}:{p}"""
                heading = "Your MBTI type is"
                meaning = "Description"
                careers = "Recommended Careers"
                bar_title = "Your Personality Traits"

            text_chart = format_text_bar_chart(scores, bar_title)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"""{heading} {mbti_result}
{meaning}: {info["description"]}
{careers}: {', '.join(info["careers"])}

{ratios}

{text_chart}"""
                )
            )
            del user_sessions[user_id]

    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="กด 'เริ่มทำแบบทดสอบ' เพื่อเริ่มทำแบบทดสอบ MBTI")
        )

def send_question(user_id, reply_token):
    session = user_sessions[user_id]
    lang = session.get("language", "th")
    qlist = questions_th if lang == "th" else questions_en
    q = qlist[session["current_question"]]
    text = q["text"] + "\n" + "\n".join([f"{k}. {v['text']}" for k, v in q["choices"].items()])
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    
mbti_descriptions_th = {
        "ENTJ": {
            "คำอธิบาย": "ผู้บัญชาการ: ผู้ที่มีความเป็นผู้นำสูง วิเคราะห์บนหลักของเหตุและผล มีความมั่นใจ และมีอิทธิพลต่อคนรอบข้าง",
            "อาชีพที่เหมาะสม": ["นักการเมือง", "ทนายความ", "อัยการ", "ผู้พิพากษา"]
        },
        "ENTP": {
            "คำอธิบาย": "นักโต้วาที: ผู้ที่มีความคิดสร้างสรรค์ ฉลาด และมีไหวพริบที่ดี ชื่นชอบการถกเถียงและวิจารณ์ประเด็นต่าง ๆ บนพื้นฐานของเหตุและผล",
            "อาชีพที่เหมาะสม": ["นักเศรษฐศาสตร์", "แพทย์", "สัตวแพทย์", "ทันตแพทย์", "เภสัชกร", "นักเทคนิคการแพทย์"]
        },
        "ENFJ": {
            "คำอธิบาย": "ผู้เป็นตัวเอก: ผู้ที่มีเสน่ห์ เข้าใจผู้อื่น มักใส่ใจความรู้สึกผู้อื่นมากเกินไป ชอบให้ความช่วยเหลือคนรอบข้าง",
            "อาชีพที่เหมาะสม": ["นักโฆษณา", "นักแสดง", "นักประชาสัมพันธ์", "มัณฑนากร", "สถาปนิก", "นางแบบ - นายแบบ", "นักจัดรายการวิทยุโทรทัศน์", "ผู้ออกแบบเครื่องแต่งกาย", "นักวิจารณ์", "ผู้ออกแบบเครื่องเรียน"]
        },
        "ENFP": {
            "คำอธิบาย": "นักรณรงค์: ผู้ที่มีความคิดสร้างสรรค์ ชอบความท้าทาย มีมนุษย์สัมพันธ์ที่ดี มักจะมีเพื่อนเยอะเพราะเข้ากับได้กับทุกคน",
            "อาชีพที่เหมาะสม": ["นักประมง", "นักเดินป่า", "พนักงานป่าไม้", "นักกีฬา", "นักเดินเรือ", "นักประดาน้ำ"]
        },
        "ESTJ": {
            "คำอธิบาย": "ผู้บริหาร: ผู้ที่มีความสามารถในการตัดสินใจอย่างมีเหตุผล เป็นกลาง ชัดเจน ลงมือปฏิบัติบนพื้นฐานของความเป็นจริงที่เป็นไปได้",
            "อาชีพที่เหมาะสม": ["นายหน้าซื้อขาย", "ที่ปรึกษาทางธุรกิจ"]
        },
        "ESTP": {
            "คำอธิบาย": "ผู้ประกอบการ: ผู้ที่มีความกระฉับกระเฉง ช่างสังเกต ชอบแข่งขัน มองเห็นรายละเอียดของสิ่งต่าง ๆ และวิเคราะห์สถานการณ์ได้เป็นอย่างดี",
            "อาชีพที่เหมาะสม": ["นักธุรกิจ", "นักการตลาด", "นักบริหาร", "ผู้จัดการ"]
        },
        "ESFJ": {
            "คำอธิบาย": "ผู้ให้คำปรึกษา: ผู้ที่มีความเห็นใจผู้อื่น มักชอบอยู่กับผู้คน เป็นที่รักของคนหมู่มาก เป็นมิตร มักได้รับความไว้วางใจจากผู้อื่น",
            "อาชีพที่เหมาะสม": ["นักแนะแนว", "ผู้ให้คำปรึกษา"]
        },
        "ESFP": {
            "คำอธิบาย": "ผู้มอบความบันเทิง: ผู้ที่ชอบความสนุกสนาน เป็นมิตร กระตือรือร้น มีทักษะทางสังคมที่ดี เข้าสังคมเก่ง",
            "อาชีพที่เหมาะสม": ["นักประดิษฐ์", "ช่างภาพ", "ช่างพิมพ์", "นักออกแบบ", "นักประพันธ์", "นักพากย์", "นักเต้นรำ", "นักเขียนการ์ตูน", "ครูสอนศิลปะ", "วาทยกร"]
        },
        "INTJ": {
            "คำอธิบาย": "นักกลยุทธ์: ผู้มีแผนการสำหรับทุกอย่าง เป็นนักคิด ช่างสังเกต ช่างจินตนาการ และมองการไกล กระหายความรู้ใหม่ ๆ",
            "อาชีพที่เหมาะสม": ["นักสถิติ", "เจ้าหน้าที่วิเคราะห์การเงิน"]
        },
        "INTP": {
            "คำอธิบาย": "นักตรรกะ: ผู้ที่มุ่งเน้นเกี่ยวกับแนวคิด ทฤษฎี หลักการที่อยู่บนความเป็นจริง ชอบสร้างสรรค์สิ่งใหม่ ๆ อย่างมีแบบแผน",
            "อาชีพที่เหมาะสม": ["นักฟิสิกส์", "นักพยาธิวิทยา", "นักวิทยาศาสตร์", "นักสถิติ", "นักชีววิทยา", "นักจุลชีววิทยา", "นักเคมี", "นักวางแผน", "นักวิชาการ"]
        },
        "INFJ": {
            "คำอธิบาย": "ผู้สนับสนุน: ผู้ที่มีความเป็นตนเองสูง ดูเป็นคนเงียบ ๆ แต่เร็วต่อความรู้สึก มีความเห็นอกเห็นใจและเข้ากับผู้อื่นได้ง่าย",
            "อาชีพที่เหมาะสม": ["ครู - อาจารย์", "นักวิชาการ"]
        },
        "INFP": {
            "คำอธิบาย": "ผู้ไกล่เกลี่ย: ผู้ที่ชอบช่วยเหลือผู้อื่น มีความซื่อสัตย์ มองสิ่งต่าง ๆ ในมุมมองที่เป็นบวก ใจกว้าง ยืดหยุ่น เคารพและรับฟังทุกความคิดเห็น",
            "อาชีพที่เหมาะสม": ["ผู้จัดการ", "บรรณารักษ์", "นักโภชนาการ", "ล่าม", "มัคคุเทศน์", "นักเทศน์"]
        },
        "ISTJ": {
            "คำอธิบาย": "นักคำนวณ: ผู้ที่วิเคราะห์สิ่งต่าง ๆ ตามความเป็นจริง คำนึงถึงสิ่งที่เป็นไปได้หรือข้อเท็จจริงมากกว่าการจินตนาการ",
            "อาชีพที่เหมาะสม": ["สมุห์บัญชี", "นักบัญชี", "เลขานุการ", "เจ้าหน้าที่ธนาคาร", "ตรวจสอบบัญชี", "เจ้าหน้าที่สารบรรณ", "ผู้ช่วยบรรณารักษ์", "เจ้าหน้าที่สรรพากร", "เจ้าหน้าที่คอมพิวเตอร์"]
        },
        "ISTP": {
            "คำอธิบาย": "ผู้เชี่ยวชาญ: ผู้ที่พัฒนาและทดลองสิ่งต่าง ๆ บนพื้นฐานของความเป็นจริง ชอบทำมากกว่าพูด แต่บางครั้งก็ทำอะไรปุบปับจนคาดเดาอารมณ์ได้ยาก",
            "อาชีพที่เหมาะสม": ["ช่างเทคนิค", "ช่างฝีมือ", "ช่างซ่อม", "ช่างฟิต", "ช่างสำรวจ", "ช่างไฟฟ้า", "ช่างยนต์", "ช่างตัดเสื้อ", "ช่างก่อสร้าง", "ช่างเครื่อง", "ช่างประปา"]
        },
        "ISFJ": {
            "คำอธิบาย": "ผู้พิทักษ์: ผู้ที่คำนึงถึงคนอื่นเสมอ รักเพื่อนพ้อง ทุ่มเทและซื่อสัตย์ให้กับคนที่ตนเองไว้ใจ มักมองหาทางออกที่ไม่ก่อให้เกิดความขัดแย้ง",
            "อาชีพที่เหมาะสม": ["พยาบาล", "นักสังคมสงเคราะห์", "นักสังคมวิทยา", "เจ้าหน้าที่งานบุคคล", "นักฝึกอบรม", "นักพัฒนากร", "ทูต"]
        },
        "ISFP": {
            "คำอธิบาย": "นักผจญภัย: ผู้ที่รักในอิสระ ชอบความสันโดษแต่ก็เข้ากับคนอื่นได้ง่าย ปรับตัวเก่ง อ่อนไหวต่อความรู้สึก",
            "อาชีพที่เหมาะสม": ["ผู้กำกับการแสดง", "ผู้สื่อข่าวเต้นรำ", "นักดนตรี", "นักโฆษณา", "นักแสดง", "นักประชาสัมพันธ์", "นางแบบ - นายแบบ", "นักจัดรายการวิทยุโทรทัศน์", "นักวิจารณ์", "จิตรกร"]
        }
    }
mbti_info_th = {
    k: {
        "description": v["คำอธิบาย"],
        "careers": v["อาชีพที่เหมาะสม"]
    }
    for k, v in mbti_descriptions_th.items()
}
mbti_info_en = {
    "ENTJ": {
        "Description": "A strong leader. They think with logic, feel confident, and can lead others.",
        "careers": ["Politician", "Lawyer", "Judge"]
    },
    "ENTP": {
        "Description": "A smart and creative person. They like to talk, ask questions, and share ideas.",
        "careers": ["Economist", "Doctor", "Vet", "Dentist", "Pharmacist", "Medical Lab Worker"]
    },
    "ENFJ": {
        "Description": "A kind and friendly person. They care about people and like to help.",
        "careers": ["Advertiser", "Actor", "PR Officer", "Interior Designer", "Architect", "Model", "TV/Radio Host", "Fashion Designer", "Critic"]
    },
    "ENFP": {
        "Description": "A fun and creative person. They enjoy new things and make friends easily.",
        "careers": ["Fisher", "Hiker", "Forest Worker", "Athlete", "Sailor", "Diver"]
    },
    "ESTJ": {
        "Description": "A clear and practical thinker. They make smart and fair decisions.",
        "careers": ["Business Broker", "Business Advisor"]
    },
    "ESTP": {
        "Description": "An active and sharp person. They see details and think fast.",
        "careers": ["Businessperson", "Marketer", "Manager"]
    },
    "ESFJ": {
        "Description": "A warm and helpful person. People trust and like them.",
        "careers": ["Career Helper", "Advisor"]
    },
    "ESFP": {
        "Description": "A fun and happy person. They love people and enjoy talking.",
        "careers": ["Inventor", "Photographer", "Printer", "Designer", "Writer", "Voice Actor", "Dancer", "Comic Artist", "Art Teacher", "Music Leader"]
    },
    "INTJ": {
        "Description": "A planner and thinker. They love to learn and have big ideas.",
        "careers": ["Statistician", "Financial Analyst"]
    },
    "INTP": {
        "Description": "A thinker who loves ideas and learning. They like to create new things.",
        "careers": ["Physicist", "Scientist", "Biologist", "Chemist", "Academic", "Planner"]
    },
    "INFJ": {
        "Description": "A quiet and caring person. They understand others well.",
        "careers": ["Teacher", "Researcher"]
    },
    "INFP": {
        "Description": "A kind and honest person. They respect others and stay positive.",
        "careers": ["Manager", "Librarian", "Nutritionist", "Tour Guide", "Interpreter", "Preacher"]
    },
    "ISTJ": {
        "Description": "A serious and careful person. They like facts and real things.",
        "careers": ["Accountant", "Secretary", "Bank Officer", "Auditor", "Clerk", "Tax Officer", "Computer Staff"]
    },
    "ISTP": {
        "Description": "A hands-on person. They like to fix and build things.",
        "careers": ["Technician", "Mechanic", "Builder", "Electrician", "Tailor", "Surveyor", "Plumber"]
    },
    "ISFJ": {
        "Description": "A gentle and loyal person. They care about people and avoid fights.",
        "careers": ["Nurse", "Social Worker", "HR Officer", "Trainer", "Peace Worker", "Diplomat"]
    },
    "ISFP": {
        "Description": "A quiet and free person. They enjoy time alone but are still friendly.",
        "careers": ["Director", "Musician", "Artist", "Actor", "PR Officer", "Model", "TV Host", "Critic", "Painter"]
    }
}
def get_mbti_info(mbti_type, lang):
    if lang == "th":
        info = mbti_info_th.get(mbti_type)
        return info or {
            "description": "ไม่พบข้อมูลบุคลิกภาพนี้",
            "careers": ["ยังไม่มีคำแนะนำอาชีพ"]
        }
    else:
        info = mbti_info_en.get(mbti_type)
        return info or {
            "description": "Unknown type",
            "careers": ["No recommended careers yet"]
        }

def save_to_google_sheet(user_id, answers, mbti_result, faculties):
    timestamp = datetime.now().isoformat()
    row = [timestamp, user_id] + answers + [mbti_result, ', '.join(faculties)]
    sheet.append_row(row)

if __name__ == "__main__":
    app.run(debug=True)


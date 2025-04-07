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
    [
  {
    "text": "ข้อ 5: คุณคิดว่าเทศกาลใดที่ทำให้คุณรู้สึกมีความสุขมากที่สุด?",
    "choices": {
      "A": { "text": "คริสต์มาสสิ เตรียมเหมาสินค้าลดราคาในห้างและฉลองกับเพื่อน", "score": "I+0" },
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
      "B": { "text": "ทักษะทางภาษา ฟัง พูด อ่าน เขียน", "score": "S+0" },
      "C": { "text": "ค้นหาสิ่งใหม่ ๆ บนพื้นฐานของวิทยาศาสตร์", "score": "S+1" },
      "D": { "text": "งานศิลปะ ดนตรี ความสวยงาม ความสุนทรีย์", "score": "N+2" },
      "E": { "text": "วัฒนธรรม ประวัติศาสตร์ การดำรงอยู่ของสังคม", "score": "N+1" }
    }
  },
  {
    "text": "ข้อ 7: ในการอ่านนิยายสักเล่ม หรือดูหนังสักเรื่อง คุณมักมีกระบวนการคิดแบบใด?",
    "choices": {
      "A": { "text": "อินไปกับเนื้อหา และอารมณ์ที่ส่งออกมาถึงตนเอง", "score": "N+2" },
      "B": { "text": "วิจารณ์ตัวละคร ว่าถ้าเป็นฉันจะทำแบบนี้", "score": "N+0" },
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
      "C": { "text": "เพื่อนแนะนำ", "score": "N+0" },
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
      "E": { "text": "ไทม์แมชชีน", "score": "S+0" }
    }
  }
[
  {
    "text": "ข้อ 11: หากคุณเห็นเพื่อนของคุณทำผิดกฎ คุณจะจัดการอย่างไร?",
    "choices": {
      "A": { "text": "รวบรวมหลักฐาน แล้วนำไปแจ้งคุณครูทันที", "score": "T+2" },
      "B": { "text": "เข้าไปตักเตือนก่อน ถ้าไม่ฟังก็นำไปแจ้งคุณครู", "score": "T+1" },
      "C": { "text": "ทำเป็นไม่รู้ไม่เห็น แต่ก็รู้สึกผิดกับตนเอง", "score": "T+0" },
      "D": { "text": "เข้าไปพูดคุยถึงเหตุผลที่ต้องทำผิด จากนั้นหาทางออกที่ดีกว่า", "score": "F+1" },
      "E": { "text": "ช่วยดูต้นทางให้ เพราะยังไงก็เป็นเพื่อนของเรา", "score": "F+2" }
    }
  },
  {
    "text": "ข้อ 12: หากคุณมีปัญหากับแฟน แม้ปัญหาไม่ได้เกิดจากคุณเองก็ตาม แต่แฟนโวยวายใส่คุณไม่หยุด คุณจะ...",
    "choices": {
      "A": { "text": "บอกไปว่า อย่าทำแบบนี้ ปัญหาไม่ได้เกิดจากฉัน", "score": "T+2" },
      "B": { "text": "บอกไปว่า ไว้เราใจเย็นทั้งคู่ค่อยคุยกันไหม", "score": "T+1" },
      "C": { "text": "เลือกที่จะเงียบ รออีกฝ่ายใจเย็นแล้วค่อยคุย", "score": "T+0" },
      "D": { "text": "เป็นฝ่ายพูดขอโทษออกไปทันที แล้วปรับความเข้าใจ", "score": "F+1" },
      "E": { "text": "โวยวายกลับ เพราะปัญหาไม่ได้เกิดจากฉัน", "score": "F+2" }
    }
  },
  {
    "text": "ข้อ 13: เวลาคุณเล่นเกมแล้วแพ้บ่อยจนทำให้ตัวเองรู้สึกโมโห คุณมีวิธีการจัดการกับอารมณ์นี้ของคุณอย่างไร?",
    "choices": {
      "A": { "text": "วิเคราะห์ว่าความโมโหของคุณเกิดจากอะไร โมโหไปแล้วได้อะไร", "score": "T+2" },
      "B": { "text": "พยายามหาวิธีคลายความโมโหของตัวเองให้เร็วที่สุด เช่น ดูหนัง ฟังเพลง", "score": "T+1" },
      "C": { "text": "กดความอารมณ์ไว้ แม้ว่าจะยังไม่หายดี แต่เราต้องไม่แสดงออก", "score": "T+0" },
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
      "A": { "text": "เดินหนี เพราะปัญหานั้นไม่ได้ส่งผลดีต่อฉัน", "score": "F+0" },
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
      "C": { "text": "ตรงบ้างสายบ้างแล้วแต่จังหวะ", "score": "J+0" },
      "D": { "text": "นัดสิบโมงตื่นสิบโมง", "score": "P+1" },
      "E": { "text": "ไปตามเวลากะเทย", "score": "P+2" }
    }
  },
  {
    "text": "ข้อ 17: ทุกครั้งที่คุณกำลังทำงานหรือวางแผนงาน มักจะมีเหตุการณ์เหล่านี้เกิดขึ้นเสมอ?",
    "choices": {
      "A": { "text": "สามารถทำงานตามแผนที่วางไว้และเสร็จได้ตรงเวลา", "score": "J+2" },
      "B": { "text": "มีการปรับเปลี่ยนแผนงานเล็กน้อยแต่ยังได้ผลลัพธ์คงเดิม", "score": "J+1" },
      "C": { "text": "เร่งทำให้เสร็จตามเวลาแม้จะข้ามบางขั้นตอนไปบ้าง", "score": "P+0" },
      "D": { "text": "ไม่ค่อยทำตามแผนที่วางไว้สักเท่าไหร่ เพราะระหว่างทางเจอแผนที่ง่ายกว่า", "score": "P+1" },
      "E": { "text": "มีความคิดมากมายผุดขึ้นมา จนบางทีก็เปลี่ยนหัวข้อกะทันหัน", "score": "P+2" }
    }
  },
  {
    "text": "ข้อ 18: หากเปรียบเทียบคุณกับตำแหน่งหน้าที่ต่อไปนี้ คุณคิดว่าคุณเป็นใคร?",
    "choices": {
      "A": { "text": "นักวางแผน เพราะคุณชอบความแน่ชัด และทำงานได้อย่างเป็นระบบ", "score": "J+2" },
      "B": { "text": "เลขานุการ แม้คุณไม่ชอบออกความคิดเห็นเท่าไหร่ แต่คุณสามารถดำเนินการตามแผนได้อย่างดี", "score": "J+1" },
      "C": { "text": "ลูกทีม งานจะเสร็จช้าหรือเร็วก็ขึ้นอยู่กับหัวหน้างานนั่นแหละ", "score": "J+0" },
      "D": { "text": "นักปรับเปลี่ยน อาจไม่ลงลอยกับนักวางแผนเท่าไหร่ แต่วิธีการฉันมันยืดหยุ่นกว่านะ", "score": "P+1" },
      "E": { "text": "คนขี้เกียจ ทำไมทุกคนไม่ทำตัวสบาย ๆ ค่อย ๆ ทำ เดี๋ยวก็เสร็จเอง งานมันไม่ไปไหนหรอก", "score": "P+2" }
    }
  },
  {
    "text": "ข้อ 19: หากคุณมีนัดที่สำคัญมาก ๆ เช่น นัดเดตกับแฟนในวันครบรอบ เป็นต้น แต่เกิดการจราจรหนาแน่นสุด ๆ คุณจะทำอย่างไร?",
    "choices": {
      "A": { "text": "ไม่ได้ส่งผลกระทบอะไรต่อคุณมาก เพราะมีแผนสำรองเสมอ", "score": "J+2" },
      "B": { "text": "เปิด GPS วางแผนและตัดสินใจอย่างรวดเร็วเพื่อหาเส้นทางที่สามารถไปได้ตรงเวลาที่สุด", "score": "J+1" },
      "C": { "text": "เลือกเส้นทางเดิม แต่โทรแจ้งอีกฝ่ายให้ทราบล่วงหน้าว่าอาจไปสายเพื่อไม่ให้เกิดการเสียความรู้สึก", "score": "J+0" },
      "D": { "text": "คุณนั่งวิเคราะห์แนวทางที่สามารถทำได้ ณ ขณะนั้น เพราะไม่ได้เตรียมแผนสำรองมาล่วงหน้า", "score": "P+1" },
      "E": { "text": "คุณตัดสินใจทันทีโดยการขึ้นวินมอเตอร์ไซค์เพื่อไปให้ถึงที่หมายโดยไม่ได้วางแผนอะไรเลย", "score": "P+2" }
    }
  },
  {
    "text": "ข้อ 20: ในขณะที่คุณกำลังทำงานชิ้นหนึ่งอยู่ แต่เพื่อนสนิทของคุณชวนไปปาร์ตี้ คุณจะทำอย่างไร?",
    "choices": {
      "A": { "text": "ปฏิเสธทันทีเพราะคุณวางแผนเอาไว้แล้ว และไม่มีใครจะมาทำลายแผนงานของคุณได้", "score": "J+2" },
      "B": { "text": "ตอบตกลง แต่บอกเพื่อนว่าจะไปช้าหน่อย เพราะมีงานที่ต้องทำให้เสร็จ", "score": "J+1" },
      "C": { "text": "บอกเพื่อนว่าอาจจะไปหรือไม่ไปก็ได้ ขึ้นอยู่กับงานที่ทำอยู่ เดี๋ยวบอกอีกที", "score": "J+0" },
      "D": { "text": "เปลี่ยนแผนงานเกือบทั้งหมดเพื่อให้งานเสร็จทันเวลา จะได้รีบไปปาร์ตี้", "score": "P+1" },
      "E": { "text": "คุณเป็นคนมีความสามารถมากพอที่จะปาร์ตี้ไปด้วยและทำงานไปด้วยได้", "score": "P+2" }
    }
  }
]

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

# เทียนไข (Candle_TS)

บอท Discord ที่อ่านข้อความในห้องแชทเป็นเสียงภาษาไทย ใช้เสียง neural ของ Azure และใช้ gTTS แทนเมื่อ Azure ใช้ไม่ได้ ตั้งค่าแยกตามเซิร์ฟเวอร์

โค้ดชุดแรกสมัยมัธยม (2021–2022) เก็บไว้ที่ tag [`v0.1.3-highschool`](https://github.com/noneykung/Candle_TS/tree/v0.1.3-highschool)

## คำสั่ง

| คำสั่ง | ทำอะไร |
|---|---|
| `/join` | เข้าห้องเสียงที่คนเรียกอยู่ |
| `/leave` | ออกจากห้องเสียง |
| `/skip` | ข้ามข้อความที่กำลังอ่าน |
| `/setup channel:<ห้อง>` | ตั้งห้องแชทที่ให้อ่าน (ไม่ใส่ห้อง = ดูค่าที่ตั้งไว้) · ต้องมีสิทธิ์ Manage Server |
| `/voice` | เลือกเสียง Premwadee / Achara / Niwat · ต้องมีสิทธิ์ Manage Server |
| `/help` | วิธีใช้ |

พิมพ์ `//` นำหน้าข้อความถ้าไม่อยากให้บอทอ่าน บอทจะออกจากห้องเองถ้าอยู่คนเดียวครบ 60 วินาที

## ตั้งค่าครั้งแรก

1. **Discord** ไปที่ [Developer Portal](https://discord.com/developers/applications) → แอปของบอท
   - Bot → Reset Token แล้วเก็บไว้
   - Bot → เปิด **Message Content Intent**
   - ลิงก์เชิญ (เปลี่ยน `<APP_ID>` เป็น Application ID):
     `https://discord.com/oauth2/authorize?client_id=<APP_ID>&scope=bot+applications.commands&permissions=3165184`
     (View Channel, Send Messages, Embed Links, Connect, Speak)
2. **Azure** (ไม่ใส่ก็ได้ ถ้าไม่ใส่จะใช้ gTTS อย่างเดียว) สร้าง Speech resource แบบ **Free F0** ใน region Southeast Asia แล้ว copy Key 1
3. copy `.env.example` เป็น `.env` แล้วกรอกค่า ใส่ `DEV_GUILD_ID` เป็น id ของเซิร์ฟเวอร์ทดสอบ คำสั่งจะขึ้นในเซิร์ฟเวอร์นั้นทันที ถ้าเว้นว่าง คำสั่งจะ sync ไปทุกเซิร์ฟเวอร์ ซึ่งอาจใช้เวลาเป็นชั่วโมง

## รันบนเครื่องตัวเอง

ใช้ Docker (มี ffmpeg อยู่ใน image แล้ว):

```
docker compose up --build
```

หรือรันด้วย Python โดยตรง (ต้องมี ffmpeg ใน PATH):

```
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
.venv\Scripts\python -m candle
```

## Deploy บน Oracle Cloud Always Free

1. สร้าง VM แบบ **Ampere A1** (ARM) image Ubuntu 24.04 ขนาด 1 OCPU / 6 GB ก็พอ บอทไม่ต้องรับการเชื่อมต่อเข้า จึงไม่ต้องเปิด port
2. SSH เข้าไปติดตั้ง Docker แล้ว clone repo:
   ```
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker $USER   # ออกแล้ว SSH เข้าใหม่
   git clone https://github.com/noneykung/Candle_TS.git candle_ts
   cd candle_ts && cp .env.example .env && nano .env
   docker compose up -d --build
   ```
3. ครั้งต่อไปให้รันจากเครื่องตัวเอง (Git Bash หรือ WSL): `./deploy.sh ubuntu@<vm-ip>`
   ถ้ายังไม่ได้ merge เข้า main ให้ใช้ `DEPLOY_BRANCH=rewrite ./deploy.sh ubuntu@<vm-ip>`

ดู log ด้วย `docker compose logs -f` log บันทึกแค่ guild id ความยาวข้อความ และ provider ที่ใช้ ไม่บันทึกเนื้อหาข้อความ ถ้าเห็น `azure quota exhausted` ทั้งที่เพิ่งเริ่มเดือน ให้เช็กว่า key กับ region ถูกต้อง

ข้อมูลตั้งค่าเก็บใน Docker volume `candle-data` backup ด้วย:

```
docker compose cp candle:/app/data/candle.db ./candle-backup.db
```

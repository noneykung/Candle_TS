# แผนรีไรท์ Candle_TS (เทียนไข)

บอท TTS ภาษาไทยบน Discord เขียนใหม่ให้ใช้ได้หลายเซิร์ฟเวอร์ ใช้เสียง neural ของ Azure เป็นหลัก มี gTTS สำรอง และ deploy ขึ้น Google Cloud e2-micro (free tier)

## การตัดสินใจ

| เรื่อง | ข้อสรุป |
|---|---|
| ภาษา / library | Python + discord.py 2.7+ (เวอร์ชันที่รองรับ DAVE voice E2EE) |
| ขนาดเป้าหมาย | ต่ำกว่า 100 เซิร์ฟเวอร์ ไม่ต้องทำ verification แต่ทุกอย่างแยกตามเซิร์ฟเวอร์ตั้งแต่แรก |
| Hosting | Google Cloud e2-micro (us-west1, x86) แบบ free tier เดิมเลือก Oracle Always Free แต่เปลี่ยน เพราะ Oracle อาจเรียกคืน VM ที่ใช้ CPU ต่ำกว่า 20% ติดกัน 7 วัน ถ้าอยากให้เสียงไวขึ้นค่อยย้ายไป VPS สิงคโปร์ |
| Voice หลัก | Azure Speech F0 เรียกผ่าน REST + `aiohttp` (ฟรี 0.5 ล้านตัวอักษรต่อเดือน ถ้าเกินจะหยุด ไม่เก็บเงินเพิ่ม) |
| Voice สำรอง | gTTS |
| ที่เก็บข้อมูล | SQLite ผ่าน `aiosqlite` เก็บไว้ใน Docker volume |
| Deploy | Docker + `docker compose` และใช้ `deploy.sh` (ยังไม่ทำ CI/CD) |
| Repo | ทำบน branch `rewrite` ลบ `text.txt` และ token ออกจาก history ด้วย `git filter-repo` |

ค่าเริ่มต้นที่ตั้งไว้: Azure region `southeastasia` เสียงเริ่มต้น `th-TH-PremwadeeNeural` ตัวเลือกใน `/voice` คือ Premwadee, Niwat และ Achara (ก่อนเขียนโค้ดต้องเทียบกับรายชื่อเสียงไทยปัจจุบันของ Azure อีกรอบ)

## สิ่งที่เจ้าของต้องทำเอง

1. Discord Developer Portal: กด **Reset Token** และเปิด **Message Content Intent**
2. Azure: สร้าง Speech resource แบบ **F0** ใน region Southeast Asia แล้วเก็บ key ไว้
3. Google Cloud: สมัครบัญชี ตั้ง budget alert และสร้าง VM e2-micro ตามขั้นตอนใน README

## Phase 0: เคลียร์ repo

- [x] สร้าง branch `rewrite`
- [x] ใช้ `git filter-repo` ลบ `text.txt` และ token ออกจาก history แล้ว force-push (ต้องถามเจ้าของก่อนลงมือ)
- [x] ลบ `tts.py`, `tts2.py`, `move.py` และไฟล์เสียงที่ไม่ได้ใช้ เก็บไว้แค่ `startup.wav`
- [x] เพิ่ม `.gitignore` สำหรับ `.env`, `*.db` และ `__pycache__/`

## Phase 1: โครงสร้าง

```
candle/
  __main__.py      # bootstrap, intents, sync commands
  config.py        # อ่าน .env (DISCORD_TOKEN, AZURE_SPEECH_KEY, AZURE_REGION, DEV_GUILD_ID)
  db.py            # aiosqlite: guild_id → tts_channel_id, voice
  normalize.py     # normalize(message) -> str
  tts/
    base.py        # TTSProvider interface
    azure.py       # REST + aiohttp, ขอเสียงเป็น Opus
    gtts_provider.py
    router.py      # fallback + จำว่าโควตาหมดจนถึงวันที่ 1 ของเดือน
  voice.py         # คิวและ player แยกตามเซิร์ฟเวอร์
  cogs/commands.py # /join /leave /setup /voice /skip /help
candle/assets/startup.wav   # ติดไปกับ package
tests/
  test_normalize.py
  test_router.py
Dockerfile
compose.yaml
.env.example
deploy.sh
README.md
```

## Phase 2: เขียนโค้ด (ตามลำดับ)

1. **`normalize.py`** ฟังก์ชันล้วนพร้อม test
   - ลิงก์ → "ลิงก์"
   - `@mention`, `#channel`, `@role` → ชื่อ
   - custom emoji และ emoji ปกติ → ตัดทิ้ง
   - `555…` → "ฮ่า ๆ"
   - ตัวอักษรที่ลากยาว เช่น `ค่าาาาา` → เหลือ 2 ตัว
   - ขึ้นต้นด้วย `//` → ไม่อ่าน
   - ถ้าคนพูดเปลี่ยนจากข้อความก่อน → นำหน้าด้วย "ชื่อ บอกว่า"
   - ยาวเกิน 200 ตัวอักษร → ตัดทิ้งส่วนที่เกิน
   - มีแค่ไฟล์แนบ → "ส่งไฟล์"
2. **TTS providers + router** พร้อม test
   - Azure error ครั้งเดียว (timeout หรือ 5xx) → ข้อความนั้นอ่านด้วย gTTS
   - Azure ตอบ 429 → พัก Azure ตาม `Retry-After` (ค่าเริ่มต้น 60 วินาที) ระหว่างนั้นใช้ gTTS เพราะ 429 อาจหมายถึง rate limit หรือ Azure รับไม่ไหวก็ได้ ไม่ได้แปลว่าโควตาหมดเสมอไป
   - Azure ตอบ 401/403 → ถือว่าโควตาหมดหรือ key ผิด ใช้ gTTS จนถึงวันที่ 1 ของเดือนถัดไป และ log ครั้งเดียว ไม่แจ้งในแชท (ยังไม่มีเอกสารยืนยันว่า F0 ตอบ 403 ตอนโควตาหมด ต้องดู log จริงหลัง deploy)
   - rate limit ของ F0 (ราว 20 request ต่อนาที) ใช้ร่วมกันทุกเซิร์ฟเวอร์
3. **`db.py`** เก็บการตั้งค่าแยกตามเซิร์ฟเวอร์
4. **`voice.py`**
   - คิวของแต่ละเซิร์ฟเวอร์มีได้สูงสุด 10 ข้อความ ถ้าเกินให้ทิ้งข้อความเก่าสุด
   - ใช้ ffmpeg แปลงเสียงเป็น 48kHz Opus
   - ถ้าห้องเสียงไม่มีคนเหลืออยู่ 60 วินาที บอทออกเอง
   - เล่น `startup.wav` ตอนเข้าห้อง
5. **Slash commands**
   - `/join`, `/leave`, `/skip`
   - `/setup channel:<ห้อง>` (ต้องมีสิทธิ์ Manage Server): ตั้งห้อง TTS ถ้าไม่ใส่ห้องจะแสดงค่าที่ตั้งอยู่
   - `/voice` (ต้องมีสิทธิ์ Manage Server): เลือกเสียงของเซิร์ฟเวอร์
   - บอทอ่านเฉพาะห้องที่ตั้งด้วย `/setup` เท่านั้น
6. **`/help`** แบบ embed ตามคาแรกเตอร์เทียนไข

กฎเรื่อง log: ส่งออก stdout บันทึกแค่ guild id, ความยาวข้อความ และ provider ที่ใช้ **ห้ามบันทึกเนื้อหาข้อความ**

## Phase 3: Deploy

- [x] `Dockerfile` ที่มี ffmpeg (ทดสอบแล้วทั้ง amd64 และ arm64)
- [x] `compose.yaml` ตั้ง `restart: unless-stopped` และ mount volume สำหรับ SQLite
- [x] `.env.example` และ `README.md` อธิบายการตั้งค่า
- [x] `deploy.sh`: SSH เข้าไป `git pull` แล้ว `docker compose up -d --build`
- [ ] ทดสอบใน dev guild (sync command เฉพาะ `DEV_GUILD_ID`) แล้วค่อย sync แบบ global

## เกณฑ์ว่าเสร็จ

- [ ] บอทอยู่ 2 เซิร์ฟเวอร์พร้อมกัน แต่ละที่อ่านคนละห้อง และข้อความไม่ข้ามไปอีกเซิร์ฟเวอร์
- [ ] พิมพ์ติดกันเร็ว ๆ แล้วบอทอ่านตามลำดับ ไม่ error
- [ ] ปิด Azure key แล้วบอทยังอ่านได้ด้วย gTTS
- [x] `pytest` ผ่านทั้งหมด

## เก็บไว้ทำ v2

- เลือกเสียงรายคน
- ฟีเจอร์ AI (คุยตอบเป็นเสียง แปลภาษา)
- เพิ่ม provider อื่น เช่น Google Chirp 3 HD
- GitHub Actions
- Verification เมื่อบอทเกิน 100 เซิร์ฟเวอร์

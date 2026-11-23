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

## Deploy บน Google Cloud (e2-micro free tier)

ใช้ e2-micro แทน Oracle เพราะ Oracle Always Free อาจเรียกคืน VM ที่ใช้ CPU ต่ำกว่า 20% ติดกัน 7 วัน ซึ่งบอท TTS เข้าข่ายแน่นอน

**1. บัญชีและงบ**
- สมัคร Google Cloud ผูกบัตร แล้วสร้าง project ใหม่
- Billing → Budgets & alerts → สร้าง budget ไว้ 1 ดอลลาร์ ถ้ามีค่าใช้จ่ายเกิดขึ้นจะได้อีเมลแจ้งทันที

**2. สร้าง VM** (Compute Engine → VM instances → Create instance ถ้าระบบขอให้เปิด API ก็กดเปิด)
- Region: **us-west1 (Oregon)** ใกล้สิงคโปร์ที่สุดในสาม region ที่ฟรี
- Machine: **E2 → e2-micro**
- Boot disk → Change: **Ubuntu 24.04 LTS (x86/64)** และเปลี่ยนชนิดดิสก์เป็น **Standard persistent disk** ขนาด **30 GB** ถ้าเป็น Balanced หรือ SSD จะไม่ฟรี
- Firewall: ไม่ต้องติ๊ก HTTP/HTTPS บอทไม่ต้องรับการเชื่อมต่อเข้า
- หน้าสร้าง VM จะแสดงค่าใช้จ่ายรายเดือนอยู่ด้วย ส่วนลด free tier จะไปหักในบิลภายหลัง

**3. SSH เข้าเครื่อง** กดปุ่ม **SSH** ในหน้า VM instances จะเปิดเทอร์มินัลในเบราว์เซอร์ จากนั้นรันตามนี้:
```
# swap 2 GB (RAM 1 GB ไม่พอตอน build image)
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Docker
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER
```
ปิดหน้าต่าง SSH แล้วกด SSH ใหม่ ให้สิทธิ์ docker มีผล จากนั้นรัน:
```
git clone -b rewrite https://github.com/noneykung/Candle_TS.git candle_ts
cd candle_ts && cp .env.example .env && nano .env
docker compose up -d --build
docker compose logs -f
```
ใน `.env` ใส่ `DISCORD_TOKEN` และเว้น `DEV_GUILD_ID` กับ `VOICE_DEBUG` ว่างไว้

**4. ปิดบอทบนเครื่องตัวเองก่อน** ถ้าใช้ token เดียวกันรันสองที่พร้อมกัน บอทจะตอบซ้ำและอ่านซ้ำ ให้รัน `docker compose down` บนเครื่องตัวเอง

**5. ตั้งค่าใหม่** DB บน VM เริ่มจากว่าง ต้องใช้ `/setup` กับ `/voice` ใหม่ในทุกเซิร์ฟเวอร์

**อัปเดตโค้ดครั้งต่อไป** มีสองวิธี
- SSH ผ่านเบราว์เซอร์ แล้วรัน `cd candle_ts && git pull && docker compose up -d --build`
- หรือรัน `deploy.sh` จากเครื่องตัวเอง (Git Bash หรือ WSL) ต้องสร้าง SSH key ก่อน (`ssh-keygen -t ed25519`) แล้วนำ public key ไปใส่ที่หน้า VM → Edit → SSH Keys จากนั้นรัน:
  ```
  DEPLOY_BRANCH=rewrite ./deploy.sh <username>@<external-ip>
  ```
  external IP แบบ ephemeral จะเปลี่ยนถ้าสั่ง stop แล้ว start VM ใหม่

ดู log ด้วย `docker compose logs -f` log บันทึกแค่ guild id ความยาวข้อความ และ provider ที่ใช้ ไม่บันทึกเนื้อหาข้อความ ถ้าเห็น `azure quota exhausted` ทั้งที่เพิ่งเริ่มเดือน ให้เช็กว่า key กับ region ถูกต้อง

ข้อมูลตั้งค่าเก็บใน Docker volume `candle-data` backup ด้วย:

```
docker compose cp candle:/app/data/candle.db ./candle-backup.db
```

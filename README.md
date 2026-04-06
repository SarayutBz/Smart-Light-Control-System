# 💡 Smart Building Light Control System

ระบบควบคุมไฟฟ้าอัจฉริยะครบวงจร ติดตั้งจริงในอาคารมหาวิทยาแม่โจ้ สาขาวิทยาการคอมพิวเตอร์ เชียงใหม่  
ครอบคลุม 12 ห้อง รองรับทั้ง Manual และ Auto mode ด้วย PIR motion sensor

Integrated Smart Electrical Control System
Installed at Computer Science, Maejo University, Chiang Mai.
Covers 12 rooms, supporting both Manual and Auto modes via PIR motion sensors.

---

## Architecture

<img width="612" height="387" alt="Image" src="https://github.com/user-attachments/assets/f225e8a9-65c7-4bfe-9bb7-73cad27d438b" />

---

## System Workflow
<img width="3684" height="7260" alt="Image" src="https://github.com/user-attachments/assets/4007b266-4edc-4760-b4a5-6b0815386a02" />

- raspi/1/{room}/control          ← รับคำสั่ง ON/OFF
- raspi/1/{room}/mode             ← เปลี่ยนโหมด MANUAL/AUTO
- raspi/1/{room}/status/request   ← ขอให้ส่งสถานะกลับมา

example Sent command: ON to raspi/1/room3/control


## Features

-  ควบคุมไฟ 12 ห้องแบบ real-time ผ่าน Web Dashboard
-  **AUTO mode** — PIR motion sensor เปิดไฟเมื่อมีคนเดินผ่าน ปิดอัตโนมัติเมื่อไม่มีการเคลื่อนไหว 20 วินาที
-  **MANUAL mode** — สั่งเปิด/ปิดไฟผ่าน Web ได้โดยตรง
-  Login + Role-based access (Firebase Authentication)
-  บันทึก activity log ลง Firebase Firestore
-  MQTT over TLS (encrypted, port 8883)
-  Responsive design รองรับ

---

## Frontend Screenshots
<div style="display: flex;">

<img width="400" height="982" alt="Image" src="https://github.com/user-attachments/assets/dd79096f-5f6b-4e40-b954-6394aa528e36" />
<img width="400" height="902" alt="Image" src="https://github.com/user-attachments/assets/bd065178-fe7c-4af6-a220-71f4697bb19b" />
<img width="300" height="791" alt="Image" src="https://github.com/user-attachments/assets/5bb4bc37-3272-488e-9b40-f4dd80afd95e" />
<img width="300" height="811" alt="Image" src="https://github.com/user-attachments/assets/a838868a-6052-491d-96d2-2b748d36c2c3" />
<img width="300" height="489" alt="Image" src="https://github.com/user-attachments/assets/8503b3bb-8241-4b2b-958f-282185ebc501" />
</div>

## Cloud Firestore Firebase
<img width="1830" height="923" alt="Image" src="https://github.com/user-attachments/assets/a52a18ff-fab2-4f15-84ab-c97333c83275" />

##  Tech Stack

| Layer | Technology |
|---|---|
| Hardware | Raspberry Pi, GPIO Relay Module, PIR Motion Sensor |
| Protocol | MQTT over TLS (HiveMQ Cloud) |
| Frontend | Vue 3, Composition API, Pinia, Vue Router |
| Auth & DB | Firebase Authentication, Firestore |
| Build Tool | Vite |
| Backend | Python, paho-mqtt |

---

##  Project Structure

```
smart-building-light-control/
├── hardware/               # Raspberry Pi GPIO control
│   ├── box1.py             # ควบคุมห้อง 1-6
│   ├── box2.py             # ควบคุมห้อง 8-13
│   ├── requirements.txt
│   └── .env.example
└── frontend/               # Vue 3 Web Dashboard
    ├── src/
    │   ├── views/
    │   │   ├── login.vue         # หน้า Login
    │   │   └── contolLight.vue   # หน้าควบคุมไฟ
    │   ├── services/
    │   │   ├── firebase.js       # Firebase config
    │   │   └── lightService.js   # Firestore logging
    │   └── stores/
    │       └── index.js          # Pinia store
    └── .env.example
```

---

##  Setup

### Hardware (Raspberry Pi)

```bash
cd hardware
pip install -r requirements.txt

cp .env.example .env
# แก้ไขค่าใน .env ให้ตรงกับ MQTT broker ของคุณ

python box1.py   # สำหรับ box1
python box2.py   # สำหรับ box2
```

### Frontend (Vue 3)

```bash
cd frontend
npm install

cp .env.example .env
# แก้ไขค่าใน .env ให้ตรงกับ MQTT และ Firebase ของคุณ

npm run dev      # Development
npm run build    # Production
```

### Environment Variables

**hardware/.env**
```
MQTT_BROKER=your-broker.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
```

**frontend/.env**
```
VITE_MQTT_BROKER=wss://your-broker.hivemq.cloud:8884/mqtt
VITE_MQTT_USERNAME=your_username
VITE_MQTT_PASSWORD=your_password
VITE_FIREBASE_API_KEY=your_api_key
...
```

---

##  GPIO Wiring

| Box | Room | GPIO Pin | อาจารย์ |
|-----|------|----------|---------|
| box1 | room1 | 12 | อ.ลงกต |
| box1 | room2 | 16 | อ.ปวีณ |
| box1 | room3 | 18 | อ.ก่อ |
| box1 | room4 | 20 | อ.กิต |
| box1 | room5 | 23 | อ.เก๋ |
| box1 | room6 | 24 | ห้องปริ้น |
| box2 | room8 | 12 | อ.สนิท |
| box2 | room9 | 16 | อ.สมนึก |
| box2 | room10 | 21 | อ.ก่องกาญ |
| box2 | room11 | 20 | ห้องว่าง |
| box2 | room12 | 23 | อ.ภานุ |
| box2 | room13 | 24 | อ.โจ |

> **Note:** Relay เป็น Active Low — `GPIO.LOW = เปิดไฟ`, `GPIO.HIGH = ปิดไฟ`

---

## MQTT Topics

| Topic | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `raspi/{box}/{room}/control` | Server → Pi | `ON` / `OFF` | สั่งเปิด/ปิดไฟ |
| `raspi/{box}/{room}/mode` | Server → Pi | `AUTO` / `MANUAL` | เปลี่ยนโหมด |
| `raspi/{box}/{room}/status` | Pi → Server | `{"mode":"MANUAL","light":"ON"}` | รายงานสถานะ |
| `raspi/{box}/{room}/status/request` | Server → Pi | `get` | ขอสถานะปัจจุบัน |

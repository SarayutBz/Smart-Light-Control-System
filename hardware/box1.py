import os
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from time import sleep, time
import json
import ssl
from dotenv import load_dotenv

load_dotenv()

# กำหนดขา GPIO สำหรับ Relay (ไฟ)
relay_pins = {
    "room1": 12,  # ห้อง อ.ลงกต   
    "room2": 16,  # ห้อง อ.ปวีณ
    "room3": 18,  # ห้อง อ.ก่อ
    "room4": 20,  # ห้อง อ.กิต
    "room5": 23,  # ห้อง อ.เก๋
    "room6": 24,  # ห้อง printer
}

# กำหนดขา GPIO สำหรับ PIR Sensor (เซ็นเซอร์จับความเคลื่อนไหว)
pir_to_relay = {
    27: "room3",  # อ.ก่อ
    10: "room5",  # อ.เก๋
    22: "room6",  # printer
    6: "room2",   # อ.ปวีณ 
    17: "room4"   # อ.กิต 
}

# ตั้งค่า GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# ตั้งค่าขา Relay เป็น OUTPUT และปิดไฟทั้งหมดก่อนเริ่มทำงาน
for pin in relay_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # Active Low (HIGH = ปิด, LOW = เปิด)

# ตั้งค่าขา PIR เป็น INPUT
for pir in pir_to_relay.keys():
    GPIO.setup(pir, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# สร้างตัวแปรเก็บโหมดของแต่ละห้อง
room_modes = {room: "MANUAL" for room in relay_pins}
last_motion_time = {room: 0 for room in relay_pins}
light_status = {room: False for room in relay_pins}

# ฟังก์ชันส่งสถานะกลับไปยัง Web UI
def publish_status(room):
    status = {
        "mode": room_modes[room],
        "light": "ON" if light_status[room] else "OFF"
    }
    client.publish(f"raspi/1/{room}/status", json.dumps(status))

# ฟังก์ชันเมื่อได้รับ MQTT Message
def on_message(client, userdata, msg):
    global room_modes, light_status
    topic_parts = msg.topic.split("/")
    
    # ตรวจสอบรูปแบบ topic ให้ถูกต้อง
    if len(topic_parts) < 4:
        return
        
    room = topic_parts[2]  # raspi/1/room/control
    command = msg.payload.decode("utf-8").strip()

    print(f"📥 ได้รับ MQTT: {msg.topic} -> {command}")

    # จัดการคำสั่งเปลี่ยนโหมด
    if topic_parts[3] == "mode":
        if room in room_modes:
            mode_value = command.upper()
            room_modes[room] = mode_value
            print(f"🔄 เปลี่ยนโหมด {room} เป็น {mode_value}")
            
            # เมื่อเปลี่ยนจาก AUTO เป็น MANUAL ให้คงสถานะไฟเดิมไว้
            # แต่เมื่อเปลี่ยนจาก MANUAL เป็น AUTO ให้ทำการเช็คสถานะ PIR ทันที
            if mode_value == "AUTO":
                for pir_pin, pir_room in pir_to_relay.items():
                    if pir_room == room and GPIO.input(pir_pin):
                        GPIO.output(relay_pins[room], GPIO.LOW)  # เปิดไฟ
                        light_status[room] = True
                        last_motion_time[room] = time()
            
            publish_status(room)
        return

    # จัดการคำสั่งควบคุมไฟในโหมด MANUAL
    if topic_parts[3] == "control" and room in relay_pins:
        if room_modes[room] == "MANUAL":
            is_on = command == "ON"
            GPIO.output(relay_pins[room], GPIO.LOW if is_on else GPIO.HIGH)
            light_status[room] = is_on
            publish_status(room)
            print(f"{room} -> {command}")
    
    # จัดการคำสั่งขอสถานะ
    if len(topic_parts) > 4 and topic_parts[3] == "status" and topic_parts[4] == "request":
        if room in room_modes:
            publish_status(room)

# ฟังก์ชันส่งสถานะเริ่มต้น
def setup_initial_status():
    # ส่งสถานะเริ่มต้นของทุกห้องไปยัง MQTT
    for room in relay_pins:
        publish_status(room)
    print("✅ ส่งสถานะเริ่มต้นเรียบร้อยแล้ว")

# เชื่อมต่อกับ HiveMQ โดยใช้ username และ password
client = mqtt.Client()

# ตั้งค่า SSL (หากใช้การเชื่อมต่อที่ปลอดภัย)
client.tls_set(ca_certs=None, certfile=None, keyfile=None)  # ถ้าไม่ใช้ไฟล์ cert ให้เว้นว่าง
client.tls_insecure_set(True)  # ต้องเปิดให้ไม่ตรวจสอบการใบรับรอง (หากไม่ใช้ cert ที่เป็นทางการ)

# ตั้งค่า username และ password
client.username_pw_set(os.getenv("MQTT_USERNAME"), password=os.getenv("MQTT_PASSWORD"))

client.on_message = on_message
client.on_connect = lambda client, userdata, flags, rc: setup_initial_status()

# เชื่อมต่อ HiveMQ
broker = os.getenv("MQTT_BROKER")
port = int(os.getenv("MQTT_PORT", 8883))
client.connect(broker, port, 60)

# Subscribe MQTT Topics
for room in relay_pins:
    client.subscribe(f"raspi/1/{room}/control")
    client.subscribe(f"raspi/1/{room}/mode")
    client.subscribe(f"raspi/1/{room}/status/request")

# Loop หลัก
try:
    client.loop_start()  # ใช้ loop_start() แทนเพื่อให้ทำงานในเทรดแยก
    
    while True:
        # จัดการโหมด AUTO
        for pir_pin, room in pir_to_relay.items():
            if room in room_modes and room_modes[room] == "AUTO":
                if GPIO.input(pir_pin):  # ตรวจพบการเคลื่อนไหว
                    print(f"👀 ตรวจพบการเคลื่อนไหวที่ {room} → เปิดไฟ!")
                    GPIO.output(relay_pins[room], GPIO.LOW)  # เปิดไฟ (Active Low)
                    last_motion_time[room] = time()
                    
                    # อัพเดทสถานะและส่งข้อมูลกลับ
                    if light_status[room] == False:
                        light_status[room] = True
                        publish_status(room)
        
        # ตรวจสอบการปิดไฟอัตโนมัติเมื่อไม่มีการเคลื่อนไหว
        for room in relay_pins.keys():
            if room_modes[room] == "AUTO" and light_status[room]:
                if time() - last_motion_time[room] > 20:  # ไม่มีการเคลื่อนไหวเกิน 20 วินาที
                    print(f"😴 ไม่มีการเคลื่อนไหวที่ {room} → ปิดไฟ!")
                    GPIO.output(relay_pins[room], GPIO.HIGH)  # ปิดไฟ (Active Low)
                    light_status[room] = False
                    publish_status(room)
        
        sleep(0.5)  # ลดเวลาดีเลย์ลงเพื่อตอบสนองไวขึ้น

except KeyboardInterrupt:
    print("\n🚪 ออกจากโปรแกรม...")

finally:
    client.loop_stop()  # หยุด MQTT loop
    GPIO.cleanup()
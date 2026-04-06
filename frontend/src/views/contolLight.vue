<template>
    <div class="container">
        <h1>CSMJU Light Control</h1>

        <div class="box-search">
            <div class="search-container">
                <input type="text" v-model="searchQuery" placeholder="ค้นหาห้อง..." class="search-input" />
                <button class="search-clear" v-if="searchQuery" @click="searchQuery = ''">
                    ล้าง
                </button>
            </div>
        </div>
        <!-- Search System -->


        <div class="grid">
            <!-- Room cards - filtered by search -->
            <div v-for="room in filteredRooms" :key="room.id" class="card" :id="room.id"
                :class="{ 'highlight': isHighlighted(room.id) }">
                <p>{{ room.name }}</p>
                <img :src="room.light === 'ON' ? BULB_ON_URL : BULB_OFF_URL" class="bulb">
                <div class="controls">
                    <label class="switch">
                        <input type="checkbox" :id="'switch-' + room.id" :checked="room.light === 'ON'"
                            @click="toggleLight(room.id, room.box)">
                        <span class="slider"></span>
                    </label>
                    <button :id="'auto-' + room.id" class="mode-btn" :class="{ 'auto-active': room.mode === 'AUTO' }"
                        @click="toggleMode(room.id, room.box)">
                        {{ room.mode === 'AUTO' ? 'Manual' : 'Auto' }}
                    </button>
                </div>
                <div class="status">
                    <span :id="'status-' + room.id">
                        โหมด: {{ room.mode === 'AUTO' ? 'Auto (PIR)' : 'Manual' }}
                    </span>
                </div>
            </div>


            <div v-if="filteredRooms.length === 0" class="no-results">
                <p>ไม่พบห้องที่ค้นหา</p>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import mqtt from 'mqtt'
import { logLightAction } from "@/services/lightService"
import { useUserStore } from "@/stores/index";

export default {
    name: 'LightControl',
    setup() {
        const BULB_ON_URL = "bulb_on.jpg"
        const BULB_OFF_URL = "bulb_off.jpg"
        const client = ref(null)
        const searchQuery = ref('')
        const highlightedRoomId = ref(null)
        const userStore = useUserStore();


        const rooms = ref([
            // Raspberry Pi: 172.17.23.52
            { id: 'room1', name: 'ห้อง อ.ลงกต', box: '1', light: 'OFF', mode: 'MANUAL' },
            { id: 'room2', name: 'ห้อง อ.ปวีณ', box: '1', light: 'OFF', mode: 'MANUAL' },
            { id: 'room3', name: 'ห้อง อ.ก่อ', box: '1', light: 'OFF', mode: 'MANUAL' },
            { id: 'room4', name: 'ห้อง อ.กิต', box: '1', light: 'OFF', mode: 'MANUAL' },
            { id: 'room5', name: 'ห้อง อ.เก๋', box: '1', light: 'OFF', mode: 'MANUAL' },
            { id: 'room6', name: 'ห้องปริ้น', box: '1', light: 'OFF', mode: 'MANUAL' },
            // 172.17.23.58
            { id: 'room8', name: 'อ.สนิท', box: '2', light: 'OFF', mode: 'MANUAL' },
            { id: 'room9', name: 'อ.สมนึก', box: '2', light: 'OFF', mode: 'MANUAL' },
            { id: 'room10', name: 'อ.ก่องกาญ', box: '2', light: 'OFF', mode: 'MANUAL' },
            { id: 'room11', name: 'ห้องว่าง', box: '2', light: 'OFF', mode: 'MANUAL' },
            { id: 'room12', name: 'อ.ภานุ', box: '2', light: 'OFF', mode: 'MANUAL' },
            { id: 'room13', name: 'อ.โจ', box: '2', light: 'OFF', mode: 'MANUAL' },
        ])

        // Filter rooms based on search query
        const filteredRooms = computed(() => {
            if (!searchQuery.value) return rooms.value

            const query = searchQuery.value.toLowerCase().trim()
            return rooms.value.filter(room =>
                room.name.toLowerCase().includes(query) ||
                room.id.toLowerCase().includes(query)
            )
        })

        // Highlight rooms after search
        watch(searchQuery, () => {
            // If there's exactly one search result, highlight it
            if (filteredRooms.value.length === 1) {
                highlightedRoomId.value = filteredRooms.value[0].id
                // Clear highlight after 2 seconds
                setTimeout(() => {
                    highlightedRoomId.value = null
                }, 2000)
            } else {
                highlightedRoomId.value = null
            }
        })

        const isHighlighted = (roomId) => {
            return roomId === highlightedRoomId.value
        }

        // Connect to MQTT broker
        const connectMqtt = () => {
            client.value = mqtt.connect(import.meta.env.VITE_MQTT_BROKER, {
                username: import.meta.env.VITE_MQTT_USERNAME,
                password: import.meta.env.VITE_MQTT_PASSWORD,
                protocol: import.meta.env.VITE_MQTT_PROTOCOL,
            })

            client.value.on('connect', () => {
                console.log('✅ MQTT Connected!')

                // Subscribe to all room status topics
                client.value.subscribe('raspi/+/+/status')

                // Listen for incoming messages
                client.value.on('message', (topic, message) => {
                    console.log('Received message:', topic, message.toString())

                    // Parse topic to get room info
                    const parts = topic.split('/')
                    if (parts.length === 4 && parts[3] === 'status') {
                        const box = parts[1]
                        const roomId = parts[2]
                        const status = JSON.parse(message.toString())

                        updateRoomStatus(roomId, status)
                    }
                })
            })
        }

        // Update room status based on MQTT message
        const updateRoomStatus = (roomId, status) => {
            const roomIndex = rooms.value.findIndex(room => room.id === roomId)
            if (roomIndex !== -1) {
                rooms.value[roomIndex].light = status.light
                rooms.value[roomIndex].mode = status.mode
            }
        }

        // Request room status
        const requestRoomStatus = (roomId, box) => {
            const topic = `raspi/${box}/${roomId}/status/request`
            sendCommand(topic, 'get')
        }

        // Send MQTT command
        const sendCommand = (topic, message) => {
            if (client.value && client.value.connected) {
                client.value.publish(topic, message)
                console.log(`Sent command: ${message} to ${topic}`)
            } else {
                console.error('MQTT client not connected')
            }
        }

        // Toggle light state
        const toggleLight = (roomId, box) => {
            const room = rooms.value.find(r => r.id === roomId)

            if (room.mode === 'AUTO') {
                alert('ไม่สามารถควบคุงไฟโดยตรงในโหมด Auto ได้ กรุณาเปลี่ยนเป็นโหมด Manual ก่อน')
                return
            }

            // Toggle light state
            const newState = room.light === 'ON' ? 'OFF' : 'ON'
            const topic = `raspi/${box}/${roomId}/control`
            logLightAction(roomId, newState)

            // Update local state (will be confirmed by MQTT status update)
            room.light = newState

            // Send command to MQTT
            sendCommand(topic, newState)
        }

        // Toggle mode between Auto and Manual
        const toggleMode = (roomId, box) => {
            const room = rooms.value.find(r => r.id === roomId)
            const newMode = room.mode === 'AUTO' ? 'MANUAL' : 'AUTO'
            const topic = `raspi/${box}/${roomId}/mode`

            // Update local state (will be confirmed by MQTT status update)
            room.mode = newMode

            // Send command to MQTT
            sendCommand(topic, newMode)

            // Request status update after 2 seconds to confirm change
            setTimeout(() => requestRoomStatus(roomId, box), 2000)
        }

        // Initialize MQTT connection when component mounts
        onMounted(() => {
            connectMqtt()

            // Add check for MQTT client status
            if (!client.value.connected) {
                console.error("MQTT client not connected.")
            }
            else {
                console.log("MQTT client connected. อิอิ")
            }
        })

        console.log("username: ", userStore.username)

        return {
            rooms,
            searchQuery,
            filteredRooms,
            BULB_ON_URL,
            BULB_OFF_URL,
            toggleLight,
            toggleMode,
            requestRoomStatus,
            isHighlighted,
            username: userStore.username
        }
    }
}
</script>

<style>
/* Import ฟอนต์จาก Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600&display=swap');

body {
    font-family: 'Prompt', sans-serif;
    text-align: center;
    background-color: #f4f4f4;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1100px;
    margin: auto;
    background: white;
    padding: 70px;
    border-radius: 15px;
    box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.2);

}

.box-search {
    display: flex;
    justify-content: end;
}

.search-container {

    margin: 20px 0;
    max-width: 500px;
}

.search-input {
    padding: 10px 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: 100%;
    font-size: 16px;
}

.search-clear {
    margin-left: 10px;
    padding: 0 15px;
    background: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

h1 {
    font-family: 'Prompt', sans-serif;
    font-size: 50px;
    font-weight: 600;
    color: #333;
    position: relative;
    display: inline-block;
    padding-bottom: 5px;
}

/* ทำให้คำว่า scmju เป็นสีฟ้า */
h1 span {
    color: #007bff;
}

/* เพิ่มขีดเส้นใต้แบบไล่สี */
h1::after {
    content: '';
    position: absolute;
    left: 50%;
    bottom: -5px;
    width: 100%;
    height: 5px;
    background: linear-gradient(to right, #007bff, #00c6ff);
    transform: translateX(-50%);
    border-radius: 5px;
    opacity: 0.8;
}

/* เพิ่ม Animation เวลาชี้เมาส์ */
h1:hover {
    color: #222;
    transition: color 0.3s ease-in-out;
}

h1:hover::after {
    width: 110%;
    transition: width 0.3s ease-in-out;
}

/* ปรับ layout ให้แถวหนึ่งมี 4 ใบ */
.grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    padding: 20px;
    justify-content: center;
}

/* ปรับขนาดกล่องให้เล็กลงนิดนึง */
.card {
    width: 230px;
    height: 350px;
    background: #323030;
    color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    transition: background 0.3s ease, color 0.3s ease, box-shadow 0.3s;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
}

.card p {
    font-size: 18px;
    font-weight: 400;
    font-family: 'Prompt', sans-serif;
}

.card .bulb {
    width: 80%;
    transition: filter 0.3s;
}

/* เปลี่ยนสีเมื่อเปิดไฟ */
.card.on {
    background-color: white;
    color: black;
    box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
}

.card.off {
    background-color: black;
    color: white;
    box-shadow: 0px 4px 15px rgba(255, 255, 255, 0.2);
}

.card:hover {
    transform: translateY(-10px);
    box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.3);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

/* ปรับปุ่มสวิตช์ให้ดูดีขึ้น */
.switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 28px;
    font-family: 'Prompt', sans-serif;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .3s;
    border-radius: 30px;
}

.slider:before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .3s;
    border-radius: 50%;
}

input:checked+.slider {
    background-color: #4caf50;
}

input:checked+.slider:before {
    transform: translateX(22px);
}

/* ส่วนควบคุม */
.controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    margin: 10px 0;
}

/* ปุ่มโหมด */
.mode-btn {
    padding: 6px 12px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    font-family: 'Prompt', sans-serif;
    font-size: 14px;
    transition: background-color 0.3s;
}

.mode-btn:hover {
    background-color: #0056b3;
}

.auto-active {
    background-color: #4caf50;
    color: white;
}

/* ส่วนแสดงสถานะ */
.status {
    margin-top: 10px;
    font-size: 14px;
    color: #f0f0f0;
}

/* ทำให้ responsive */
@media (max-width: 1024px) {
    .grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 768px) {
    .grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .grid {
        grid-template-columns: repeat(1, 1fr);
    }
}
</style>
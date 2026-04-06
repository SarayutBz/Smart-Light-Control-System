// src/services/lightService.js
import { db } from "./firebase";  // Import db from the firebase.js file
// import { db } from "../views/contolLight.vue";
import { collection, doc, setDoc } from "firebase/firestore";

// ฟังก์ชันบันทึกข้อมูลการเปิด-ปิดไฟ โดยการกำหนด id ของเอกสารเอง
const logLightAction = async (roomId, status) => {
    try {
        // สร้างเอกสารใหม่พร้อมกับ id ที่ต้องการ
        const docId = `${roomId}_${new Date().toISOString()}`;  // ใช้ roomId และ timestamp เป็น id
        const collectionRef = collection(db, "light_logs");
        const docRef = doc(collectionRef, docId);  // ระบุ id เอง

        // บันทึกข้อมูล
        await setDoc(docRef, {
            roomId,
            status,
            timestamp: new Date()
        });

        console.log("✅ บันทึกข้อมูลสำเร็จ");
    } catch (error) {
        console.error("❌ บันทึกข้อมูลล้มเหลว:", error);
    }
}

// Function to retrieve light logs
const getLightLogs = async () => {
    const logs = [];
    try {
        const q = query(collectionRef, orderBy("timestamp", "desc"));
        const querySnapshot = await getDocs(q);
        querySnapshot.forEach((doc) => {
            logs.push({ id: doc.id, ...doc.data() });
        });
    } catch (error) {
        console.error("❌ ดึงข้อมูลล้มเหลว:", error);
    }
    return logs;
};

export { logLightAction, getLightLogs };

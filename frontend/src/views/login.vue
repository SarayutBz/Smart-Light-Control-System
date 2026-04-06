<template>
  <div class="container">
    <div class="login-box">
      <h1 class="title">Login</h1>
      <p class="subtitle">Login with your username</p>
      <div class="form-box">
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label>Username</label>
            <input
              type="text"
              v-model="username"
              placeholder="Enter your username"
              required
            />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input
              type="password"
              v-model="password"
              placeholder="Enter your password"
              required
            />
          </div>
          <button type="submit" class="login-button">Login</button>
          <p v-if="error" class="error-message">{{ error }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";

import { collection, query, where, getDocs } from "firebase/firestore";
import { useRouter } from "vue-router"; // ใช้ Vue Router
import { useUserStore } from "@/stores/index";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth, db } from "@/services/firebase";
import { doc, getDoc } from "firebase/firestore";

export default {
  setup() {
    const userStore = useUserStore();
    const username = ref("");
    const password = ref("");
    const error = ref("");
    const router = useRouter();

    const handleLogin = async () => {
      try {
        error.value = "";

        const q = query(
          collection(db, "users"),
          where("name", "==", username.value),
          where("password", "==", password.value)
        );

        const snap = await getDocs(q);

        if (snap.empty) {
          error.value = "❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง";
          return;
        }

        const userData = snap.docs[0].data();

        console.log("Login success:", userData);

        // ตัวอย่างเช็ค role
        if (userData.role === "superadmin") {
          router.push("/controlLight");
        } else {
          error.value = "❌ ไม่มีสิทธิ์เข้าใช้งาน";
        }
      } catch (err) {
        console.error(err);
        error.value = "เกิดข้อผิดพลาด";
      }
    };
    return { username, password, error, handleLogin };
  },
};
</script>

<style scoped>
.container {
  height: 500px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #6f82d6 0%, #4ba0a2 100%);
  font-family: "Poppins", sans-serif;
}

.login-box {
  background: white;
  padding: 3rem;
  border-radius: 20px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
  text-align: center;
  max-width: 400px;
  width: 100%;
  animation: fadeIn 0.8s ease-in-out;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #333;
}

.subtitle {
  color: #777;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #444;
}

@media screen and (min-width: 560px) {
  .form-group input {
    width: 23.2rem;
    padding: 0.8rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    outline: none;
    transition: border 0.3s;
  }
}

@media screen and (min-width: 461px) and (max-width: 560px) {
  .form-group input {
    width: 15rem;
    padding: 0.8rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    outline: none;
    transition: border 0.3s;
  }
}

@media screen and (min-width: 411px) and (max-width: 460px) {
  .form-group input {
    width: 10rem;
    padding: 0.8rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    outline: none;
    transition: border 0.3s;
  }
}

@media screen and (max-width: 400px) {
  .form-group input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    outline: none;
    transition: border 0.3s;
  }
}

.form-group input:focus {
  border: 1px solid #667eea;
}

.login-button {
  background: #667eea;
  color: white;
  padding: 0.8rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
  width: 100%;
  font-weight: 600;
}

.login-button:hover {
  background: #660dec;
}

.error-message {
  color: red;
  margin-top: 1rem;
  font-weight: bold;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

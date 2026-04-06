import { createRouter, createWebHistory } from 'vue-router'
import ControlLight from '../views/contolLight.vue'
import Login from '../views/login.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/controlLight',
      name: 'controlLight',
      component: ControlLight,
    },
    {
      path: '/',
      name: 'login',
      component: Login,
    },
  ],
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    }
    // TODO: Add more routes
    // {
    //   path: '/login',
    //   name: 'login',
    //   component: () => import('../views/LoginView.vue')
    // },
    // {
    //   path: '/files',
    //   name: 'files',
    //   component: () => import('../views/FilesView.vue')
    // }
  ]
})

export default router

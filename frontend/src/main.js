import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import axios from 'axios'

import App from './App.vue'
import Map from './views/Map.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Share from './views/Share.vue'
import Friends from './views/Friends.vue'

// 路由配置
const routes = [
  { path: '/', name: 'Map', component: Map },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/share/:shareId', name: 'Share', component: Share },
  { path: '/friends', name: 'Friends', component: Friends }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 配置 axios 请求拦截器
axios.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    
    // 明确检查 token 是否存在，只有存在时才添加到请求头
    // 避免添加空值或 undefined
    if (token && token.trim()) {
      config.headers['Authorization'] = `Bearer ${token}`
    } else {
      // 如果 token 不存在，确保 Authorization 头被移除
      delete config.headers['Authorization']
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 添加响应拦截器，处理无效token的情况
axios.interceptors.response.use(
  response => response,
  error => {
    // 处理401未授权错误
    if (error.response && error.response.status === 401) {
      // 清除可能存在的无效token
      localStorage.removeItem('token')
      localStorage.removeItem('currentUser')
      
      // 可以选择重定向到登录页面
      // window.location.href = '/login?sessionExpired=true'
    }
    return Promise.reject(error)
  }
)

// 创建应用实例
const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 将axios挂载到Vue实例上
app.config.globalProperties.$axios = axios

// 使用插件
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

// 挂载应用
app.mount('#app')

console.log('🎨 城事绘图 Urban Canvas 启动成功')
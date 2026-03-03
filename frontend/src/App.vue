<template>
  <div id="app">
    <!-- 导航栏 -->
    <el-header v-if="showHeader" class="app-header">
      <div class="header-content">
        <div class="brand">
          <router-link to="/" class="brand-link">
            <h1>🗺️ 城事绘图</h1>
          </router-link>
        </div>
        
        <div class="nav-menu">
          <router-link to="/" class="nav-item">地图</router-link>
          <router-link to="/friends" class="nav-item">好友</router-link>
        </div>
        
        <div class="user-actions">
          <template v-if="currentUser">
            <span class="welcome">欢迎, {{ currentUser.username }}</span>
            <el-button @click="logout" size="small">退出</el-button>
          </template>
          <template v-else>
            <router-link to="/login">
              <el-button size="small">登录</el-button>
            </router-link>
            <router-link to="/register">
              <el-button type="primary" size="small">注册</el-button>
            </router-link>
          </template>
        </div>
      </div>
    </el-header>
    
    <!-- 主要内容区域 -->
    <main class="main-content" :class="{ 'with-header': showHeader }">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentUser = ref(null)

// 计算是否显示头部导航
const showHeader = computed(() => {
  return true // 所有页面都显示导航栏
})

// 从localStorage获取用户信息
const loadUser = () => {
  const userData = localStorage.getItem('currentUser')
  if (userData) {
    currentUser.value = JSON.parse(userData)
  }
}

// 退出登录
const logout = () => {
  // 立即清除用户状态
  currentUser.value = null
  
  // 彻底清除localStorage中的所有用户相关数据
  localStorage.removeItem('currentUser')
  localStorage.removeItem('token')
  
  // 使用强制刷新来确保页面完全重新加载，避免缓存问题
  window.location.href = '/login?loggedOut=true'
}

// 应用初始化
onMounted(() => {
  loadUser()
  
  // 监听用户登录状态变化
  window.addEventListener('userLogin', (event) => {
    currentUser.value = event.detail
  })
})
</script>

<style scoped>
.app-header {
  background: white;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 60px;
  padding: 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-link {
  text-decoration: none;
  color: inherit;
}

.brand h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #409eff;
}

.nav-menu {
  display: flex;
  gap: 20px;
}

.nav-item {
  text-decoration: none;
  color: #606266;
  padding: 8px 16px;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-item:hover,
.nav-item.router-link-active {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome {
  color: #606266;
  font-size: 14px;
}

.main-content {
  min-height: 100vh;
}

.main-content.with-header {
  min-height: calc(100vh - 60px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 15px;
  }
  
  .nav-menu {
    display: none;
  }
  
  .brand h1 {
    font-size: 1.2rem;
  }
  
  .user-actions {
    gap: 8px;
  }
  
  .welcome {
    display: none;
  }
}
</style>
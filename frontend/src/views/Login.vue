<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>🗺️ 城事绘图</h1>
        <p>登录到你的账户</p>
      </div>
      
      <el-form 
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        
        <el-button 
          type="primary" 
          size="large" 
          @click="handleSubmit"
          :loading="loading"
          class="login-btn"
        >
          登录
        </el-button>
      </el-form>
      
      <div class="login-footer">
        <p>
          还没有账号？
          <router-link to="/register" class="register-link">
            立即注册
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    loading.value = true

    const response = await axios.post('/api/auth/login', {
      username: form.username,
      password: form.password
    })
    
    // 保存用户信息和token到localStorage
    localStorage.setItem('currentUser', JSON.stringify(response.data.user))
    localStorage.setItem('token', response.data.token)
    
    // 触发用户登录事件
    window.dispatchEvent(new CustomEvent('userLogin', {
      detail: {
        user: response.data.user,
        token: response.data.token
      }
    }))
    
    ElMessage.success('登录成功！')
    router.push('/')
    
  } catch (error) {
    const message = error.response?.data?.error || '登录失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 2rem;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.login-header p {
  color: #606266;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

.login-footer {
  text-align: center;
}

.login-footer p {
  color: #606266;
  margin: 0;
}

.register-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
}

.register-link:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-container {
    padding: 30px 20px;
  }
  
  .login-header h1 {
    font-size: 1.5rem;
  }
}
</style>
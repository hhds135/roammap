<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <h1>🗺️ 城事绘图</h1>
        <p>加入我们，开始你的城市探索之旅</p>
      </div>
      
      <el-form 
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
        class="register-form"
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
          />
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
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
          class="register-btn"
        >
          注册
        </el-button>
      </el-form>
      
      <div class="register-footer">
        <p>
          已有账号？
          <router-link to="/login" class="login-link">
            立即登录
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
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    loading.value = true
    
    const response = await axios.post('/api/auth/register', {
      username: form.username,
      password: form.password
    })
    
    ElMessage.success('注册成功！请登录')
    router.push('/login')
    
  } catch (error) {
    const message = error.response?.data?.error || '注册失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-container {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.register-header h1 {
  font-size: 2rem;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.register-header p {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.register-form {
  margin-bottom: 24px;
}

.register-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

.register-footer {
  text-align: center;
}

.register-footer p {
  color: #606266;
  margin: 0;
}

.login-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
}

.login-link:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .register-container {
    padding: 30px 20px;
  }
  
  .register-header h1 {
    font-size: 1.5rem;
  }
}
</style>
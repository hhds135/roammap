<template>
  <div class="home-page">
    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          发现城市的
          <span class="highlight">隐藏角落</span>
        </h1>
        <p class="hero-description">
          在这张由集体共同绘制的地图上，像进行一场"数字寻宝"一样，
          探索他人分享的地点，发现你所在城市的独特魅力。
        </p>
        <div class="hero-actions">
          <el-button 
            type="primary" 
            size="large" 
            @click="$router.push('/map')"
            class="cta-button"
          >
            <el-icon><Location /></el-icon>
            开始探索
          </el-button>
          <el-button 
            size="large" 
            @click="$router.push('/register')"
            class="secondary-button"
          >
            <el-icon><UserFilled /></el-icon>
            加入我们
          </el-button>
        </div>
      </div>
    </section>

    <!-- 特色功能 -->
    <section class="features-section">
      <div class="container">
        <h2 class="section-title">为什么选择城事绘图？</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">🗺️</div>
            <h3>交互式地图</h3>
            <p>直观的全屏地图界面，自由缩放和平移，轻松探索每一个角落</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📖</div>
            <h3>故事分享</h3>
            <p>不只是位置标记，每个角落都有独特的照片和个人故事</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h3>智能发现</h3>
            <p>通过标签筛选和搜索功能，快速找到感兴趣的地点类型</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">👥</div>
            <h3>社区驱动</h3>
            <p>用户生成内容，真实的城市体验，来自本地人的推荐</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 最新角落 -->
    <section class="recent-section">
      <div class="container">
        <h2 class="section-title">最新发现</h2>
        <div class="corners-grid" v-loading="loading">
          <div 
            v-for="corner in recentCorners" 
            :key="corner.id"
            class="corner-card"
            @click="viewCorner(corner)"
          >
            <div class="corner-image">
              <img :src="corner.image_url" :alt="corner.title" />
            </div>
            <div class="corner-content">
              <h4>{{ corner.title }}</h4>
              <p>{{ corner.description.substring(0, 80) }}...</p>
              <div class="corner-tags">
                <el-tag 
                  v-for="tag in corner.tags.slice(0, 2)" 
                  :key="tag"
                  size="small"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        
        <div class="empty-state" v-if="!loading && recentCorners.length === 0">
          <el-empty description="暂无角落分享">
            <el-button type="primary" @click="$router.push('/map')">
              成为第一个分享者
            </el-button>
          </el-empty>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Location, UserFilled } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const recentCorners = ref([])

// 获取最新角落
const fetchRecentCorners = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/corners')
    recentCorners.value = response.data.corners.slice(0, 6)
  } catch (error) {
    console.error('获取角落失败:', error)
  } finally {
    loading.value = false
  }
}

// 查看角落详情
const viewCorner = (corner) => {
  ElMessage.info(`查看角落: ${corner.title}`)
}

onMounted(() => {
  fetchRecentCorners()
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

/* 英雄区域 */
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 100px 20px;
  text-align: center;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: bold;
  line-height: 1.2;
  margin-bottom: 24px;
}

.highlight {
  background: linear-gradient(45deg, #f093fb, #f5576c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-description {
  font-size: 1.25rem;
  line-height: 1.6;
  margin-bottom: 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  opacity: 0.9;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.cta-button {
  background: linear-gradient(45deg, #f093fb, #f5576c);
  border: none;
  padding: 16px 32px;
  font-weight: 600;
}

.secondary-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

/* 通用样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 48px;
  color: #303133;
}

/* 特色功能区域 */
.features-section {
  padding: 80px 0;
  background: white;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 32px;
}

.feature-card {
  text-align: center;
  padding: 32px 24px;
  border-radius: 12px;
  background: #f8fafc;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  background: white;
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 24px;
}

.feature-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: #303133;
}

.feature-card p {
  color: #606266;
  line-height: 1.6;
}

/* 最新角落区域 */
.recent-section {
  padding: 80px 0;
  background: #f8fafc;
}

.corners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.corner-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.corner-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.corner-image {
  height: 200px;
  overflow: hidden;
}

.corner-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.corner-content {
  padding: 20px;
}

.corner-content h4 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.corner-content p {
  color: #606266;
  line-height: 1.5;
  margin-bottom: 12px;
}

.corner-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-description {
    font-size: 1.125rem;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .hero-actions .el-button {
    width: 200px;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .corners-grid {
    grid-template-columns: 1fr;
  }
}
</style>
<template>
  <div class="share-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h2>{{ error.title || '出错了' }}</h2>
      <p>{{ error.message || '无法加载分享内容' }}</p>
      <router-link to="/" class="btn-primary">返回首页</router-link>
    </div>

    <!-- 角落详情 -->
    <div v-else-if="corner" class="corner-detail">
      <!-- 头部信息 -->
      <div class="corner-header">
        <h1 class="corner-title">{{ corner.title }}</h1>
        <div class="corner-meta">
          <span class="corner-date">{{ formatDate(corner.created_at) }}</span>
          <div class="corner-stats">
            <span class="stat-item">
              ❤️ {{ corner.likes || 0 }}
            </span>
          </div>
        </div>
      </div>

      <!-- 角落图片 -->
      <div class="corner-image-container">
        <img 
          :src="corner.image_url" 
          :alt="corner.title" 
          class="corner-image"
          @error="handleImageError"
        />
      </div>

      <!-- 角落内容 -->
      <div class="corner-content">
        <!-- 描述 -->
        <div class="corner-description">
          <h3>关于这个角落</h3>
          <p>{{ corner.description }}</p>
        </div>

        <!-- 位置信息 -->
        <div class="corner-location" v-if="corner.address || corner.latitude || corner.longitude">
          <h3>位置信息</h3>
          <p v-if="corner.address">{{ corner.address }}</p>
          <p v-if="corner.latitude && corner.longitude" class="coordinates">
            📍 {{ corner.latitude.toFixed(6) }}, {{ corner.longitude.toFixed(6) }}
          </p>
        </div>

        <!-- 标签 -->
        <div class="corner-tags" v-if="corner.tags && corner.tags.length > 0">
          <h3>标签</h3>
          <div class="tags-container">
            <span v-for="tag in corner.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>

        <!-- 评论区 -->
        <div class="corner-comments" v-if="corner.comments && corner.comments.length > 0">
          <h3>评论 ({{ corner.comments.length }})</h3>
          <div class="comments-list">
            <div v-for="comment in corner.comments" :key="comment.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-author">{{ comment.username }}</span>
                <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <router-link to="/" class="btn-secondary">
          浏览更多角落
        </router-link>
        <button v-if="isAuthenticated" @click="goToLoginAndLike" class="btn-primary">
          登录并点赞
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SharePage',
  data() {
    return {
      corner: null,
      loading: true,
      error: null,
      isAuthenticated: false
    }
  },
  computed: {
    shareId() {
      return this.$route.params.shareId
    }
  },
  mounted() {
    // 检查用户是否已登录
    this.checkAuth()
    // 加载角落数据
    this.loadCornerData()
  },
  methods: {
    checkAuth() {
      // 检查localStorage中是否有token或用户信息
      this.isAuthenticated = !!localStorage.getItem('token') || !!localStorage.getItem('currentUser')
    },
    async loadCornerData() {
      if (!this.shareId) {
        this.error = {
          title: '无效链接',
          message: '分享链接不完整，请检查链接是否正确'
        }
        this.loading = false
        return
      }

      try {
        this.loading = true
        const response = await this.$axios.get(`/api/share/${this.shareId}`)
        this.corner = response.data.corner
        this.error = null
      } catch (err) {
        console.error('加载角落数据失败:', err)
        this.error = {
          title: '加载失败',
          message: err.response?.data?.error || '无法加载分享内容，请稍后重试'
        }
        this.corner = null
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      try {
        const date = new Date(dateString)
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (e) {
        return dateString
      }
    },
    handleImageError(event) {
      // 设置默认图片或隐藏图片
      event.target.style.display = 'none'
    },
    goToLoginAndLike() {
      // 保存当前分享页面的路径，登录后可以跳转回来
      localStorage.setItem('redirectAfterLogin', window.location.href)
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.share-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8f9fa;
}

/* 加载状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误状态样式 */
.error-container {
  text-align: center;
  padding: 60px 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-top: 40px;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-container h2 {
  color: #e74c3c;
  margin-bottom: 12px;
}

/* 角落详情样式 */
.corner-detail {
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 30px;
}

.corner-header {
  padding: 24px 24px 0;
}

.corner-title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin: 0 0 12px 0;
  line-height: 1.3;
}

.corner-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}

.corner-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.corner-image-container {
  width: 100%;
  height: 400px;
  overflow: hidden;
  background-color: #f0f0f0;
}

.corner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.corner-image:hover {
  transform: scale(1.02);
}

.corner-content {
  padding: 24px;
}

.corner-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.corner-description p {
  color: #555;
  line-height: 1.6;
  margin: 0 0 24px 0;
  font-size: 16px;
}

.corner-location {
  margin-bottom: 24px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.coordinates {
  font-size: 14px;
  color: #666;
  margin: 8px 0 0;
}

.corner-tags {
  margin-bottom: 24px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  display: inline-block;
  padding: 6px 12px;
  background-color: #e9ecef;
  color: #495057;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.corner-comments {
  margin-bottom: 24px;
}

.comments-list {
  border-top: 1px solid #e9ecef;
}

.comment-item {
  padding: 16px 0;
  border-bottom: 1px solid #f1f3f5;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-author {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.comment-time {
  color: #999;
  font-size: 12px;
}

.comment-content {
  color: #555;
  line-height: 1.5;
  font-size: 15px;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 24px;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  outline: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background-color: #4a90e2;
  color: white;
}

.btn-primary:hover {
  background-color: #357abd;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(74, 144, 226, 0.3);
}

.btn-secondary {
  background-color: #ffffff;
  color: #4a90e2;
  border: 2px solid #4a90e2;
}

.btn-secondary:hover {
  background-color: #f0f7ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(74, 144, 226, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .share-container {
    padding: 12px;
  }
  
  .corner-title {
    font-size: 24px;
  }
  
  .corner-image-container {
    height: 300px;
  }
  
  .corner-content {
    padding: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .corner-image-container {
    height: 250px;
  }
  
  .corner-title {
    font-size: 20px;
  }
  
  .corner-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
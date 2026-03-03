<template>
  <div class="friends-page">
    <div class="friends-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1>👥 好友管理</h1>
        <p>管理你的社交关系，发现更多好友</p>
      </div>

      <!-- 搜索用户区域 -->
      <div class="search-section">
        <h2>🔍 搜索用户</h2>
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="输入用户名搜索..."
            prefix-icon="Search"
            clearable
            @keyup.enter="searchUsers"
          />
          <el-button type="primary" @click="searchUsers" :loading="searching">
            搜索
          </el-button>
        </div>
        
        <!-- 搜索结果 -->
        <div class="search-results" v-if="showSearchResults">
          <h3>搜索结果</h3>
          <div class="users-list" v-loading="searching">
            <div 
              v-for="user in searchResults" 
              :key="user.id"
              class="user-item"
            >
              <div class="user-info">
                <el-avatar :size="40">
                  {{ user.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <span class="username">{{ user.username }}</span>
              </div>
              <div class="user-actions">
                <el-button 
                  v-if="user.is_friend"
                  type="default"
                  disabled
                >
                  已是好友
                </el-button>
                <el-button 
                  v-else-if="user.has_pending_request"
                  type="info"
                  disabled
                >
                  请求已发送
                </el-button>
                <el-button 
                  v-else
                  type="primary"
                  @click="sendFriendRequest(user.id)"
                  :loading="sendingRequest === user.id"
                >
                  发送请求
                </el-button>
              </div>
            </div>
            <div v-if="!searching && searchResults.length === 0" class="empty-results">
              <el-empty description="未找到匹配的用户" :image-size="60"></el-empty>
            </div>
          </div>
        </div>
      </div>

      <!-- 好友请求区域 -->
      <div class="requests-section">
        <h2>📋 好友请求</h2>
        <div class="requests-list" v-loading="loadingRequests">
          <div 
            v-for="request in friendRequests" 
            :key="request.id"
            class="request-item"
          >
            <div class="user-info">
              <el-avatar :size="40">
                {{ request.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ request.username }}</span>
            </div>
            <div class="request-actions">
              <el-button 
                type="primary"
                size="small"
                @click="handleFriendRequest(request.id, 'accept')"
                :loading="handlingRequest === request.id"
              >
                接受
              </el-button>
              <el-button 
                type="default"
                size="small"
                @click="handleFriendRequest(request.id, 'reject')"
                :loading="handlingRequest === request.id"
              >
                拒绝
              </el-button>
            </div>
          </div>
          <div v-if="!loadingRequests && friendRequests.length === 0" class="empty-requests">
            <el-empty description="暂无好友请求" :image-size="60"></el-empty>
          </div>
        </div>
      </div>

      <!-- 好友列表区域 -->
      <div class="friends-section">
        <h2>👥 我的好友</h2>
        <div class="friends-list" v-loading="loadingFriends">
          <div 
            v-for="friend in friends" 
            :key="friend.id"
            class="friend-item"
          >
            <div class="user-info">
              <el-avatar :size="40">
                {{ friend.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ friend.username }}</span>
            </div>
            <div class="friend-actions">
              <el-button 
                type="primary"
                size="small"
                @click="viewFriendCorners(friend.id, friend.username)"
                :loading="loadingFriendCorners === friend.id"
              >
                查看角落
              </el-button>
              <el-button 
                type="danger"
                size="small"
                @click="confirmRemoveFriend(friend.id, friend.username)"
                :loading="removingFriend === friend.id"
              >
                删除好友
              </el-button>
            </div>
          </div>
          <div v-if="!loadingFriends && friends.length === 0" class="empty-friends">
            <el-empty description="暂无好友，快去添加吧！" :image-size="60">
              <el-button type="primary" @click="scrollToSearch">
                搜索用户
              </el-button>
            </el-empty>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 好友角落列表对话框 -->
    <el-dialog
      v-model="showFriendCorners"
      :title="`${currentFriend?.username || ''} 的角落`"
      width="80%"
      top="5vh"
    >
      <div class="friend-corners-list" v-loading="loadingFriendCorners">
        <div 
          v-for="corner in friendCorners" 
          :key="corner.id"
          class="corner-item"
          @click="viewCornerOnMap(corner)"
          style="cursor: pointer"
        >
          <div class="corner-image">
            <img :src="corner.image_url" :alt="corner.title" />
          </div>
          <div class="corner-content">
            <h4>{{ corner.title }}</h4>
            <p>{{ corner.description.substring(0, 80) }}...</p>
            <div class="corner-meta">
              <span class="corner-time">{{ new Date(corner.created_at).toLocaleString('zh-CN') }}</span>
              <span class="corner-likes">{{ corner.likes }} 赞</span>
            </div>
            <div class="corner-tags">
              <el-tag 
                v-for="tag in corner.tags.slice(0, 3)" 
                :key="tag"
                size="small"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
        <div v-if="!loadingFriendCorners && friendCorners.length === 0" class="empty-corners">
          <el-empty description="暂无角落" :image-size="60"></el-empty>
        </div>
      </div>
      <template #footer>
        <el-button @click="closeFriendCorners">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const searchQuery = ref('')
const searchResults = ref([])
const showSearchResults = ref(false)
const searching = ref(false)
const sendingRequest = ref(null)
const handlingRequest = ref(null)
const removingFriend = ref(null)

const friends = ref([])
const friendRequests = ref([])
const loadingFriends = ref(false)
const loadingRequests = ref(false)

// 好友角落相关
const friendCorners = ref([])
const currentFriend = ref(null)
const loadingFriendCorners = ref(null)
const showFriendCorners = ref(false)

// 获取认证配置
const getAuthConfig = () => {
  const token = localStorage.getItem('token')
  if (token) {
    return { headers: { Authorization: `Bearer ${token}` } }
  }
  return {}
}

// 搜索用户
const searchUsers = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  try {
    const response = await axios.get('/api/users/search', {
      ...getAuthConfig(),
      params: { q: searchQuery.value.trim() }
    })
    searchResults.value = response.data.users
    showSearchResults.value = true
  } catch (error) {
    ElMessage.error('搜索失败，请重试')
  } finally {
    searching.value = false
  }
}

// 发送好友请求
const sendFriendRequest = async (userId) => {
  sendingRequest.value = userId
  try {
    await axios.post('/api/friends/request', 
      { receiver_id: userId },
      getAuthConfig()
    )
    ElMessage.success('好友请求已发送')
    // 更新搜索结果中的状态
    const user = searchResults.value.find(u => u.id === userId)
    if (user) {
      user.has_pending_request = true
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '发送请求失败')
  } finally {
    sendingRequest.value = null
  }
}

// 处理好友请求
const handleFriendRequest = async (userId, action) => {
  handlingRequest.value = userId
  try {
    await axios.put(`/api/friends/request/${userId}`,
      { action },
      getAuthConfig()
    )
    ElMessage.success(action === 'accept' ? '好友请求已接受' : '好友请求已拒绝')
    // 从请求列表中移除
    friendRequests.value = friendRequests.value.filter(r => r.id !== userId)
    // 如果是接受，重新加载好友列表
    if (action === 'accept') {
      loadFriends()
    }
  } catch (error) {
    ElMessage.error('处理请求失败，请重试')
  } finally {
    handlingRequest.value = null
  }
}

// 确认删除好友
const confirmRemoveFriend = (friendId, friendName) => {
  ElMessageBox.confirm(
    `确定要删除好友 ${friendName} 吗？`,
    '删除好友',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    removeFriend(friendId)
  }).catch(() => {
    // 取消删除
  })
}

// 删除好友
const removeFriend = async (friendId) => {
  removingFriend.value = friendId
  try {
    await axios.delete(`/api/friends/${friendId}`, getAuthConfig())
    ElMessage.success('好友已删除')
    // 从好友列表中移除
    friends.value = friends.value.filter(f => f.id !== friendId)
  } catch (error) {
    ElMessage.error('删除好友失败，请重试')
  } finally {
    removingFriend.value = null
  }
}

// 加载好友列表
const loadFriends = async () => {
  loadingFriends.value = true
  try {
    const response = await axios.get('/api/friends', getAuthConfig())
    friends.value = response.data.friends
  } catch (error) {
    ElMessage.error('加载好友列表失败')
  } finally {
    loadingFriends.value = false
  }
}

// 加载好友请求列表
const loadFriendRequests = async () => {
  loadingRequests.value = true
  try {
    const response = await axios.get('/api/friends/requests', getAuthConfig())
    friendRequests.value = response.data.requests
  } catch (error) {
    ElMessage.error('加载好友请求失败')
  } finally {
    loadingRequests.value = false
  }
}

// 滚动到搜索区域
const scrollToSearch = () => {
  const searchSection = document.querySelector('.search-section')
  if (searchSection) {
    searchSection.scrollIntoView({ behavior: 'smooth' })
  }
}

// 查看好友角落
const viewFriendCorners = async (friendId, friendName) => {
  loadingFriendCorners.value = friendId
  currentFriend.value = { id: friendId, username: friendName }
  
  try {
    const response = await axios.get(`/api/friends/${friendId}/corners`)
    friendCorners.value = response.data.corners
    showFriendCorners.value = true
    ElMessage.success(`已加载 ${friendCorners.value.length} 个角落`)
  } catch (error) {
    console.error('加载好友角落失败:', error)
    ElMessage.error(error.response?.data?.error || '加载失败，请重试')
  } finally {
    loadingFriendCorners.value = null
  }
}

// 关闭好友角落列表
const closeFriendCorners = () => {
  showFriendCorners.value = false
  friendCorners.value = []
  currentFriend.value = null
}

// 查看角落在地图上的位置
const viewCornerOnMap = (corner) => {
  console.log('查看角落在地图上的位置:', corner.title)
  
  // 将角落信息存储到localStorage中
  localStorage.setItem('viewCorner', JSON.stringify(corner))
  
  // 跳转到地图页面
  window.location.href = '/'
}

// 生命周期
onMounted(() => {
  loadFriends()
  loadFriendRequests()
})
</script>

<style scoped>
.friends-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

/* 好友角落列表样式 */
.friend-corners-list {
  max-height: 60vh;
  overflow-y: auto;
}

.corner-item {
  display: flex;
  gap: 20px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  background: #fafafa;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.corner-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.corner-image {
  flex-shrink: 0;
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
}

.corner-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.corner-content {
  flex: 1;
  min-width: 0;
}

.corner-content h4 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.corner-content p {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.corner-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #909399;
}

.corner-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-corners {
  text-align: center;
  padding: 40px 0;
}

/* 好友操作按钮样式 */
.friend-actions {
  display: flex;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .friend-corners-list {
    max-height: 50vh;
  }
  
  .corner-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .corner-image {
    width: 100%;
    height: 200px;
  }
  
  .corner-content {
    width: 100%;
  }
  
  .friend-actions {
    flex-direction: column;
    align-items: flex-end;
  }
}

/* 滚动条样式 */
.friend-corners-list::-webkit-scrollbar {
  width: 6px;
}

.friend-corners-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.friend-corners-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.friend-corners-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.friends-container {
  max-width: 800px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 2rem;
}

.page-header p {
  color: #606266;
  font-size: 1.1rem;
}

.search-section,
.requests-section,
.friends-section {
  margin-bottom: 40px;
  padding: 20px;
  background: #fafafa;
  border-radius: 12px;
  border: 1px solid #ebeef5;
}

.search-section h2,
.requests-section h2,
.friends-section h2 {
  color: #303133;
  margin-bottom: 20px;
  font-size: 1.3rem;
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-bar .el-input {
  flex: 1;
}

.search-results h3 {
  color: #303133;
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.users-list,
.requests-list,
.friends-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-item,
.request-item,
.friend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: white;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  transition: all 0.3s ease;
}

.user-item:hover,
.request-item:hover,
.friend-item:hover {
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  border-color: #409eff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.user-actions,
.request-actions,
.friend-actions {
  display: flex;
  gap: 8px;
}

.empty-results,
.empty-requests,
.empty-friends {
  text-align: center;
  padding: 40px 20px;
}

@media (max-width: 768px) {
  .friends-container {
    padding: 20px;
  }
  
  .search-bar {
    flex-direction: column;
  }
  
  .user-item,
  .request-item,
  .friend-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .user-actions,
  .request-actions,
  .friend-actions {
    align-self: flex-end;
  }
}
</style>
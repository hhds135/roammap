<template>
  <div class="map-page">
    <!-- 左侧面板 -->
    <div class="left-panel">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <div class="header-row">
          <div class="brand-info">
            <h2>🗺️ 城事绘图</h2>
            <p>发现城市的隐藏角落，分享你的故事</p>
          </div>
          <div class="user-status" v-if="currentUser">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ currentUser.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ currentUser.username }}</span>
            </div>
            <el-dropdown trigger="click" class="user-dropdown">
              <el-button type="text" class="dropdown-trigger">
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <div class="tip-section" v-if="currentUser">
          <el-alert
            title="💡 点击地图任意位置创建新角落"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
        <div class="tip-section" v-else>
          <el-alert
            title="请先登录后分享角落"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <el-button type="text" @click="$router.push('/login')" style="padding: 0; color: #e6a23c;">
                立即登录
              </el-button>
            </template>
          </el-alert>
        </div>
      </div>
      
      <!-- 我的角落和收藏 -->
      <div class="recent-section">
        <div class="section-header">
          <el-tabs v-model="activeTab" @tab-click="handleTabClick" class="corner-tabs">
            <el-tab-pane label="我的角落" name="myCorners">
              <span class="tab-badge">{{ myCorners.length }}</span>
            </el-tab-pane>
            <el-tab-pane label="我的收藏" name="myFavorites">
              <span class="tab-badge">{{ myFavorites.length }}</span>
            </el-tab-pane>
          </el-tabs>
        </div>
        <div class="corners-list" v-loading="loading">
          <div 
            v-for="corner in activeTab === 'myCorners' ? myCorners : myFavorites" 
            :key="corner.id"
            class="corner-item"
          >
            <div class="corner-main" @click="viewCornerOnMap(corner)">
              <div class="corner-image">
                <img :src="corner.image_url" :alt="corner.title" />
              </div>
              <div class="corner-content">
                <h4>{{ corner.title }}</h4>
                <p>{{ corner.description.substring(0, 60) }}...</p>
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
            <!-- 操作按钮 -->
            <div class="corner-actions" v-if="activeTab === 'myCorners' && currentUser && corner.user_id === currentUser.id">
              <el-button 
                type="primary" 
                size="small" 
                @click.stop="editCorner(corner)"
                circle
                icon="Edit"
                :title="'编辑角落'"
              >
              </el-button>
              <el-popconfirm
                confirm-button-text="确认"
                cancel-button-text="取消"
                icon="el-icon-warning"
                icon-color="#f90"
                title="确定要删除这个角落吗？"
                @confirm="deleteCorner(corner.id)"
              >
                <template #reference>
                  <el-button 
                    type="danger" 
                    size="small" 
                    circle
                    icon="Delete"
                    :title="'删除角落'"
                  >
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </div>
        
        <div class="empty-state" v-if="!loading && (activeTab === 'myCorners' ? myCorners.length === 0 : myFavorites.length === 0)">
          <el-empty :description="activeTab === 'myCorners' ? '暂无角落分享' : '暂无收藏的角落'" :image-size="60">
            <el-button type="primary" @click="startSharing" v-if="currentUser && activeTab === 'myCorners'">
              成为第一个分享者
            </el-button>
            <el-button type="primary" @click="$router.push('/register')" v-else-if="activeTab === 'myCorners'">
              注册后分享
            </el-button>
          </el-empty>
        </div>
      </div>
    </div>
    
    <!-- 地图容器 -->
    <div id="map" class="map-container"></div>
    
    <!-- 地图控制面板 -->
    <div class="map-controls">
      <!-- 组合搜索区域 -->
      <div class="search-panel">
        <div class="search-row">
          <el-input
            v-model="searchQuery"
            placeholder="搜索地点或角落..."
            prefix-icon="Search"
            clearable
            @keyup.enter="handleCombinedSearch"
            class="search-input"
          />
          <el-select
            v-model="selectedTags"
            placeholder="选择标签（支持模糊搜索）"
            multiple
            filterable
            default-first-option
            collapse-tags
            collapse-tags-tooltip
            clearable
            @change="handleCombinedSearch"
            class="tag-select"
            :popper-append-to-body="false"
          >
            <template v-for="(tag, index) in displayTags" :key="tag">
              <el-option
                :label="tag"
                :value="tag"
              />
            </template>
          </el-select>
          <el-button type="primary" @click="handleCombinedSearch" :loading="searching">
            搜索
          </el-button>
          <!-- 定位按钮集成到搜索行 -->
          <el-button 
            @click="locateUser"
            :loading="locating"
            class="location-btn-inline"
            circle
            :title="'定位我的位置'"
          >
            <el-icon><Aim /></el-icon>
          </el-button>
        </div>
        <div class="search-status" v-if="searchQuery || selectedTags.length > 0 || friendsOnly.value">
          <span class="search-info">
            <template v-if="friendsOnly.value">
              <el-tag type="primary" size="small">仅好友</el-tag>
            </template>
            <template v-if="searchQuery && selectedTags.length > 0">
              搜索: "{{ searchQuery }}" + 标签: {{ selectedTags.join(', ') }}
            </template>
            <template v-else-if="searchQuery">
              搜索: "{{ searchQuery }}"
            </template>
            <template v-else-if="selectedTags.length > 0">
              标签: {{ selectedTags.join(', ') }}
            </template>
          </span>
          <el-button type="text" @click="clearSearch" size="small">
            清除筛选
          </el-button>
        </div>
        <!-- 仅好友开关 -->
        <div class="friends-only-toggle">
          <el-switch
            v-model="friendsOnly"
            active-text="仅好友"
            inactive-text="全世界"
            @change="handleFriendsOnlyChange"
          />
        </div>
      </div>
    </div>
    

    
    <!-- 分享/编辑对话框 -->
    <el-dialog
      v-model="showShareDialog"
      :title="isEditMode ? '编辑角落' : '分享新角落'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="shareFormRef"
        :model="shareForm"
        :rules="shareRules"
        label-width="80px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="shareForm.title" placeholder="给这个角落起个名字" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="shareForm.description"
            type="textarea"
            :rows="3"
            placeholder="分享这个角落的故事..."
          />
        </el-form-item>
        
        <el-form-item label="照片" prop="image">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageChange"
            accept="image/*"
            drag
          >
            <div v-if="!imagePreview" class="upload-area">
              <el-icon class="upload-icon"><Plus /></el-icon>
              <div>点击或拖拽上传照片</div>
            </div>
            <div v-else class="image-preview">
              <img :src="imagePreview" alt="预览" />
            </div>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="地址">
          <el-input v-model="shareForm.address" placeholder="地址描述（可选）" />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select
            v-model="shareFormTags"
            placeholder="选择标签（支持模糊搜索）"
            multiple
            filterable
            default-first-option
            collapse-tags
            collapse-tags-tooltip
            class="tag-select"
            :popper-append-to-body="false"
          >
            <template v-for="(tag, index) in displayTags" :key="tag">
              <el-option
                :label="tag"
                :value="tag"
              />
            </template>
          </el-select>
          <div class="tag-tip">
            <small>提示：请从预设标签中选择</small>
          </div>
        </el-form-item>
        
        <el-form-item label="位置">
          <div class="location-info">
            <small>纬度: {{ shareForm.latitude?.toFixed(6) }}</small><br>
            <small>经度: {{ shareForm.longitude?.toFixed(6) }}</small>
          </div>
        </el-form-item>
        
        <el-form-item label="隐私设置" prop="visibility">
          <el-select v-model="shareForm.visibility" placeholder="选择可见性" class="w-full">
            <el-option label="公开（所有人可见）" value="public" />
            <el-option label="仅自己可见" value="private" />
            <el-option label="仅好友可见" value="friends" />
            <el-option label="指定好友可见" value="specific_friends" />
            <el-option label="指定好友不可见" value="exclude_friends" />
          </el-select>
          <!-- 指定好友选择 -->
          <div v-if="shareForm.visibility === 'specific_friends' || shareForm.visibility === 'exclude_friends'" class="friends-selection">
            <el-select
              v-model="selectedFriends"
              multiple
              placeholder="选择好友"
              class="w-full"
              style="margin-top: 10px"
            >
              <el-option
                v-for="friend in friendsList"
                :key="friend.id"
                :label="friend.username"
                :value="friend.id"
              />
            </el-select>
            <small v-if="shareForm.visibility === 'specific_friends'" class="help-text">
              只有选中的好友可以看到此角落
            </small>
            <small v-else-if="shareForm.visibility === 'exclude_friends'" class="help-text">
              除了选中的好友外，其他人都可以看到此角落
            </small>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="cancelSharing">取消</el-button>
        <el-button type="primary" @click="submitShare" :loading="submitting">
          {{ isEditMode ? '保存修改' : '分享角落' }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 角落详情对话框 -->
    <el-dialog
      v-model="showCornerDetail"
      :title="selectedCorner?.title"
      width="500px"
    >
      <div v-if="selectedCorner" class="corner-detail">
        <div class="corner-image">
          <img :src="selectedCorner.image_url" :alt="selectedCorner.title" />
        </div>
        <div class="corner-content">
          <!-- 隐私角落标识 -->
          <div v-if="selectedCorner.privacy && currentUser && selectedCorner.user_id === currentUser.id" class="privacy-badge">
            <el-tag size="small" type="warning">隐私角落</el-tag>
          </div>
          <p>{{ selectedCorner.description }}</p>
          <div class="corner-meta">
            <p><strong>地址:</strong> {{ selectedCorner.address || '未提供' }}</p>
            <p><strong>分享时间:</strong> {{ formatDate(selectedCorner.created_at) }}</p>
          </div>
          <div class="corner-tags">
            <el-tag 
              v-for="tag in selectedCorner.tags" 
              :key="tag"
              style="margin-right: 8px;"
            >
              {{ tag }}
            </el-tag>
          </div>
          <!-- 互动操作区域 -->
            <div class="interaction-section">
              <div class="like-button-wrapper">
                <el-button 
                  :type="isLiked ? 'danger' : 'default'" 
                  :icon="isLiked ? 'StarFilled' : 'Star'" 
                  circle
                  @click="handleLike"
                  :disabled="!currentUser"
                  :loading="liking"
                  class="like-button"
                  :class="{ 'liked': isLiked }"
                >
                </el-button>
                <span class="like-count" :class="{ 'like-count-active': isLiked }">
                  {{ selectedCorner?.likes || 0 }}
                </span>
              </div>
              <div class="favorite-button-wrapper">
                <el-button 
                  :type="isFavorited ? 'primary' : 'default'" 
                  :icon="isFavorited ? 'StarFilled' : 'Star'" 
                  circle
                  @click="handleFavorite"
                  :disabled="!currentUser"
                  :loading="favoriting"
                  class="favorite-button"
                  :class="{ 'favorited': isFavorited }"
                >
                </el-button>
                <span class="favorite-text" :class="{ 'favorite-text-active': isFavorited }">
                  收藏
                </span>
              </div>
              <!-- 分享按钮 -->
              <div class="share-button-wrapper">
                <el-button 
                  type="success"
                  :icon="'Share'"
                  circle
                  @click="handleShare"
                  :loading="sharing"
                  class="share-button"
                >
                </el-button>
                <span class="share-text">
                  分享
                </span>
              </div>
              <span v-if="!currentUser" class="login-tip">请登录后互动</span>
            </div>
          
          <!-- 评论区域 -->
          <div class="comments-section">
            <h4>评论 ({{ (selectedCorner.comments || []).length }})</h4>
            
            <!-- 评论输入框 -->
            <div v-if="currentUser" class="comment-input-section">
              <el-input
                v-model="commentText"
                placeholder="写下你的评论..."
                type="textarea"
                :rows="2"
                @keyup.enter.ctrl="submitComment"
              ></el-input>
              <div class="comment-actions">
                <span class="comment-tip">按 Ctrl+Enter 发送</span>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="submitComment"
                  :disabled="!commentText.trim() || commenting"
                  :loading="commenting"
                >
                  发送评论
                </el-button>
              </div>
            </div>
            <div v-else class="login-to-comment">
              <el-button type="text" @click="$router.push('/login')">
                登录后发表评论
              </el-button>
            </div>
            
            <!-- 评论列表 -->
            <div class="comments-list" v-if="selectedCorner.comments && selectedCorner.comments.length > 0">
              <div 
                v-for="comment in selectedCorner.comments" 
                :key="comment.id"
                class="comment-item"
              >
                <div class="comment-header">
                  <div class="comment-main">
                    <el-avatar :size="24">
                      {{ comment.username.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <div class="comment-info">
                      <span class="comment-username">{{ comment.username }}</span>
                      <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
                    </div>
                  </div>
                  <!-- 只对自己的评论显示删除按钮 -->
                  <el-popconfirm
                    v-if="currentUser && currentUser.id === comment.user_id"
                    confirm-button-text="确认"
                    cancel-button-text="取消"
                    icon="el-icon-warning"
                    icon-color="#f90"
                    title="确定要删除这条评论吗？"
                    @confirm="handleDeleteComment(selectedCorner.id, comment.id)"
                  >
                    <template #reference>
                      <el-button 
                        type="text" 
                        size="small"
                        class="delete-button"
                      >
                        删除
                      </el-button>
                    </template>
                  </el-popconfirm>
                </div>
                <div class="comment-content">{{ comment.content }}</div>
              </div>
            </div>
            <div v-else class="no-comments">
              <el-empty description="暂无评论，快来发表第一条评论吧！" :image-size="40"></el-empty>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
    
    <!-- 分享链接对话框 -->
    <el-dialog
      v-model="showShareLinkDialog"
      title="分享角落"
      width="400px"
    >
      <div class="share-link-content">
        <p>复制以下链接分享给他人：</p>
        <el-input 
          v-model="shareLink" 
          readonly
          class="share-link-input"
        >
          <template #append>
            <el-button @click="copyShareLink" type="primary" size="small">
              复制
            </el-button>
          </template>
        </el-input>
        <p class="share-tip">分享后，任何人无需登录即可查看此角落信息</p>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.share-link-content {
  padding: 10px 0;
}

.share-link-input {
  margin: 15px 0;
}

.share-tip {
  color: #606266;
  font-size: 12px;
  margin-top: 10px;
}

.friends-selection {
  margin-top: 12px;
}

.help-text {
  color: #909399;
  font-size: 12px;
  display: block;
  margin-top: 6px;
}

/* 隐私徽章样式 */
.privacy-badge {
  margin-bottom: 10px;
}

/* 标签选择器样式 */
.tag-select {
  width: 100%;
}

/* 分页控件样式 */
.tags-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
}

.page-info {
  margin: 0 15px;
  color: #606266;
}
</style>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Aim, ArrowDown, SwitchButton, Plus, Share } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import axios from 'axios'

// 响应式数据
const map = ref(null)
const searchQuery = ref('')
const selectedTags = ref([])
const availableTags = ref([])
const searching = ref(false)
const showShareDialog = ref(false)
const showCornerDetail = ref(false)
const selectedCorner = ref(null)
const submitting = ref(false)
const imagePreview = ref('')
const shareFormRef = ref()
const uploadRef = ref()
const currentUser = ref(null)
const corners = ref([])
const markers = ref([])
const recentCorners = ref([])
const loading = ref(false)
const locating = ref(false)
const userLocationMarker = ref(null)
const showingSearchResults = ref(false)
const pendingLocation = ref(null)
const pendingMarker = ref(null)
// 标签切换相关数据
const activeTab = ref('myCorners')
const myCorners = ref([])
const myFavorites = ref([])
// 编辑模式相关数据
const isEditMode = ref(false)
const currentEditCornerId = ref(null)
// 仅好友模式
const friendsOnly = ref(false)
// 标签展示相关数据
const displayLimit = ref(5)
const displayTags = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const filteredTags = ref([])
const tagSearchQuery = ref('')
// 点赞和评论相关数据
const commentText = ref('')
const liking = ref(false)
const commenting = ref(false)
// 分享相关数据
const sharing = ref(false)
const shareLink = ref('')
const showShareLinkDialog = ref(false)

const getAuthConfig = () => {
  const token = localStorage.getItem('token')
  if (token) {
    return { headers: { Authorization: `Bearer ${token}` } }
  }
  return {}
}

// 分享表单
const shareForm = reactive({
  title: '',
  description: '',
  address: '',
  tags: '',
  latitude: null,
  longitude: null,
  image: null,
  visibility: 'public', // 默认公开
  specific_friends: [], // 指定可见的好友ID列表
  exclude_friends: [] // 指定不可见的好友ID列表
})

// 好友选择相关
const friendsList = ref([])
const selectedFriends = ref([])

// 分享表单标签数组（用于多选组件）
const shareFormTags = ref([])

// 表单验证规则
const shareRules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ]
}

// 地图初始化
const initMap = () => {
  map.value = L.map('map', {
    center: [52.4862, -1.8904], // 伯明翰坐标
    zoom: 13
  })
  
  // 添加地图图层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value)
  
  // 地图点击事件
  map.value.on('click', handleMapClick)
  
  // 加载角落数据
  loadCorners()
  loadTags()
}

// 加载角落数据
const loadCorners = async () => {
  loading.value = true
  try {
    // 不再需要显式传递user_id参数，会通过JWT自动获取用户信息
    const response = await axios.get('/api/corners', getAuthConfig())
    let allCorners = response.data.corners
    
    // 根据仅好友模式过滤
    corners.value = filterFriendsCorners(allCorners)
    recentCorners.value = corners.value.slice(0, 6)
    showingSearchResults.value = false
    updateMapMarkers()
    // 更新我的角落和收藏
    updateMyCornersAndFavorites()
  } catch (error) {
    console.error('加载角落失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载我的收藏
const loadMyFavorites = async () => {
  if (!currentUser.value) {
    myFavorites.value = []
    return
  }
  
  try {
    const response = await axios.get(`/api/users/${currentUser.value.id}/favorites`, getAuthConfig())
    let favorites = response.data.corners || []
    
    // 根据仅好友模式过滤
    myFavorites.value = filterFriendsCorners(favorites)
  } catch (error) {
    console.error('加载收藏失败:', error)
    myFavorites.value = []
  }
}

// 更新我的角落和收藏
const updateMyCornersAndFavorites = () => {
  if (!currentUser.value) {
    myCorners.value = []
    myFavorites.value = []
    return
  }
  
  // 过滤出我的角落
  myCorners.value = corners.value.filter(corner => {
    return corner.user_id === currentUser.value.id
  })
  
  // 加载我的收藏
  loadMyFavorites()
}

// 处理标签切换
const handleTabClick = () => {
  if (activeTab.value === 'myFavorites' && currentUser.value) {
    loadMyFavorites()
  }
}

// 处理仅好友开关变化
const handleFriendsOnlyChange = () => {
  console.log('仅好友模式:', friendsOnly.value)
  // 重新加载角落数据
  loadCorners()
}

// 过滤好友角落
const filterFriendsCorners = (cornersList) => {
  if (!friendsOnly.value || !currentUser.value) {
    return cornersList
  }
  
  // 获取好友ID列表
  const friendIds = friendsList.value.map(friend => friend.id)
  // 包括自己
  const userIds = [...friendIds, currentUser.value.id]
  
  // 过滤出好友和自己的角落
  return cornersList.filter(corner => {
    return userIds.includes(corner.user_id)
  })
}

// 加载标签数据
const loadTags = async () => {
  try {
    const response = await axios.get('/api/tags')
    availableTags.value = response.data.tags
    // 直接显示所有标签，不再分页
    displayTags.value = availableTags.value
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

// 更新显示的标签
const updateDisplayTags = () => {
  displayTags.value = tagSearchQuery.value ? filteredTags.value : availableTags.value
}

// 处理标签搜索过滤
const handleTagFilterChange = (query) => {
  tagSearchQuery.value = query
  
  if (query && query.trim()) {
    // 过滤标签
    filteredTags.value = availableTags.value.filter(tag => 
      tag.toLowerCase().includes(query.toLowerCase())
    )
  } else {
    // 清空过滤
    filteredTags.value = []
  }
  
  // 重置到第一页
  currentPage.value = 1
  // 更新显示的标签
  updateDisplayTags()
}

// 处理标签选择下拉菜单显示/隐藏
const handleTagSelectVisible = (visible) => {
  if (!visible) {
    // 当下拉菜单关闭时，重置搜索状态
    tagSearchQuery.value = ''
    filteredTags.value = []
    // 重置到第一页
    currentPage.value = 1
    // 更新显示的标签
    updateDisplayTags()
  }
}

// 更新地图标记
const updateMapMarkers = () => {
  // 清除现有标记
  markers.value.forEach(marker => {
    map.value.removeLayer(marker)
  })
  markers.value = []
  
  // 添加新标记
  corners.value.forEach(corner => {
    const marker = L.marker([corner.latitude, corner.longitude])
      .addTo(map.value)
      .bindPopup(`
        <div style="text-align: center;">
          <img src="${corner.image_url}" alt="${corner.title}" style="width: 150px; height: 100px; object-fit: cover; border-radius: 4px;" />
          <h4 style="margin: 8px 0 4px 0;">${corner.title}</h4>
          <p style="margin: 0; font-size: 12px; color: #666;">${corner.description.substring(0, 50)}...</p>
        </div>
      `)
      .on('click', () => {
        selectedCorner.value = corner
        showCornerDetail.value = true
        // 加载点赞和收藏状态
        loadCornerDetail(corner.id)
      })
    
    markers.value.push(marker)
  })
}

// 地图点击处理
const handleMapClick = (e) => {
  console.log('地图点击坐标:', e.latlng.lat, e.latlng.lng) // 调试信息
  
  if (showShareDialog.value) {
    // 如果分享对话框已经打开，更新坐标
    shareForm.latitude = e.latlng.lat
    shareForm.longitude = e.latlng.lng
    ElMessage.success(`位置已更新: ${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`)
    return
  }
  
  if (!currentUser.value) {
    // 用户未登录，提示登录
    ElMessage.warning('请先登录后再分享角落')
    return
  }
  
  // 显示新建角落选项弹窗
  const clickedLat = e.latlng.lat
  const clickedLng = e.latlng.lng
  
  ElMessageBox.confirm(
    '是否在此位置创建新角落？',
    '新建角落',
    {
      confirmButtonText: '创建角落',
      cancelButtonText: '取消',
      type: 'info',
      center: true
    }
  ).then(async () => {
    // 用户确认创建角落
    console.log('用户确认创建角落，开始加载好友列表...')
    
    // 加载好友列表
    await loadFriends()
    
    Object.assign(shareForm, {
      title: '',
      description: '',
      address: '',
      tags: '',
      latitude: clickedLat,
      longitude: clickedLng,
      image: null,
      visibility: 'public',
      specific_friends: [],
      exclude_friends: []
    })
    imagePreview.value = ''
    // 清空标签选择
    shareFormTags.value = []
    // 清空好友选择
    selectedFriends.value = []
    
    showShareDialog.value = true
    ElMessage.success('开始创建新角落！')
    console.log('分享对话框打开，好友列表:', friendsList.value)
  }).catch(() => {
    // 用户取消
    ElMessage.info('已取消创建')
  })
}



// 清除待确认位置状态
const clearPendingLocation = () => {
  if (pendingMarker.value) {
    map.value.removeLayer(pendingMarker.value)
    pendingMarker.value = null
  }
  pendingLocation.value = null
}

// 处理分享功能
const handleShare = async () => {
  if (!selectedCorner.value) return
  
  sharing.value = true
  try {
    // 调用API生成/获取分享链接
    const response = await axios.post(`/api/corners/${selectedCorner.value.id}/share-link`)
    const shareId = response.data.share_id
    
    // 生成完整的分享URL
    const baseUrl = window.location.origin
    shareLink.value = `${baseUrl}/share/${shareId}`
    
    // 显示分享链接对话框
    showShareLinkDialog.value = true
  } catch (error) {
    console.error('生成分享链接失败:', error)
    ElMessage.error('生成分享链接失败，请重试')
  } finally {
    sharing.value = false
  }
}

// 复制分享链接
const copyShareLink = () => {
  navigator.clipboard.writeText(shareLink.value).then(() => {
    ElMessage.success('分享链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

// 组合搜索处理
const handleCombinedSearch = async () => {
  searching.value = true
  try {
    const params = {}
    
    // 添加文本搜索参数
    if (searchQuery.value && searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }
    
    // 添加多标签筛选参数
    if (selectedTags.value && selectedTags.value.length > 0) {
      params.tags = selectedTags.value.join(',')
    }
    
    const response = await axios.get('/api/corners', { ...getAuthConfig(), params })
    let searchResults = response.data.corners
    
    // 根据仅好友模式过滤
    corners.value = filterFriendsCorners(searchResults)
    recentCorners.value = corners.value
    showingSearchResults.value = true
    updateMapMarkers()
    
    // 显示搜索结果信息
    const resultCount = corners.value.length
    if (params.search || params.tags) {
      ElMessage.success(`找到 ${resultCount} 个匹配的角落`)
    }
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

// 清除搜索筛选
const clearSearch = async () => {
  searchQuery.value = ''
  selectedTags.value = []
  
  // 重新加载所有角落
  try {
    const response = await axios.get('/api/corners', getAuthConfig())
    corners.value = response.data.corners
    recentCorners.value = response.data.corners.slice(0, 6)
    showingSearchResults.value = false
    updateMapMarkers()
    ElMessage.info('已清除所有筛选条件')
  } catch (error) {
    ElMessage.error('加载数据失败')
  }
}

// 保留原有的单独搜索方法以兼容其他可能的调用
const handleSearch = handleCombinedSearch
const handleTagFilter = handleCombinedSearch

// 退出登录
const logout = () => {
  currentUser.value = null
  localStorage.removeItem('currentUser')
  ElMessage.success('已退出登录')
  // 刷新页面以重置状态
  location.reload()
}

// 加载好友列表
const loadFriends = async () => {
  if (!currentUser.value) return
  
  try {
    // 直接使用axios，拦截器会自动添加token
    const response = await axios.get('/api/friends')
    friendsList.value = response.data.friends || []
    console.log('好友列表加载成功:', friendsList.value)
    ElMessage.success(`已加载 ${friendsList.value.length} 个好友`)
  } catch (error) {
    console.error('加载好友列表失败:', error)
    ElMessage.error('加载好友列表失败，请稍后重试')
    friendsList.value = []
  }
}

// 开始分享
const startSharing = async () => {
  console.log('开始分享，当前用户:', currentUser.value)
  console.log('LocalStorage token:', localStorage.getItem('token'))
  
  if (!currentUser.value) {
    ElMessage.warning('请先登录')
    return
  }
  
  // 加载好友列表
  console.log('开始加载好友列表...')
  await loadFriends()
  
  // 重置表单
    Object.assign(shareForm, {
      title: '',
      description: '',
      address: '',
      tags: '',
      latitude: map.value.getCenter().lat,
      longitude: map.value.getCenter().lng,
      image: null,
      visibility: 'public',
      specific_friends: [],
      exclude_friends: []
    })
    imagePreview.value = ''
    // 清空标签选择
    shareFormTags.value = []
    // 清空好友选择
    selectedFriends.value = []
    
    showShareDialog.value = true
    ElMessage.info('请在地图上点击选择具体位置')
    console.log('分享对话框打开，好友列表:', friendsList.value)
}

// 取消分享
const cancelSharing = () => {
  showShareDialog.value = false
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  // 清空标签选择
  shareFormTags.value = []
  // 重置编辑模式
  isEditMode.value = false
  currentEditCornerId.value = null
}

// 图片上传处理
const handleImageChange = (file) => {
  shareForm.image = file.raw
  
  // 创建预览
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

// 提交分享或编辑
const submitShare = async () => {
  if (!shareFormRef.value) return
  
  try {
    const valid = await shareFormRef.value.validate()
    if (!valid) return
    
    if (!shareForm.image && !isEditMode.value) {
      ElMessage.error('请上传照片')
      return
    }
    
    if (!shareForm.latitude || !shareForm.longitude) {
        ElMessage.error('请在地图上选择位置')
        return
    }
    
    submitting.value = true
    
    // 将标签数组转换为逗号分隔的字符串
    if (shareFormTags.value.length > 0) {
        shareForm.tags = shareFormTags.value.join(',')
    }
    
    // 处理好友选择
    if (shareForm.visibility === 'specific_friends') {
        shareForm.specific_friends = selectedFriends.value
    } else if (shareForm.visibility === 'exclude_friends') {
        shareForm.exclude_friends = selectedFriends.value
    }
    
    const formData = new FormData()
    formData.append('title', shareForm.title)
    formData.append('description', shareForm.description)
    formData.append('address', shareForm.address)
    formData.append('tags', shareForm.tags)
    formData.append('latitude', shareForm.latitude)
    formData.append('longitude', shareForm.longitude)
    formData.append('user_id', currentUser.value.id)
    if (shareForm.image) {
      formData.append('image', shareForm.image)
    }
    formData.append('visibility', shareForm.visibility)
    formData.append('specific_friends', shareForm.specific_friends.join(','))
    formData.append('exclude_friends', shareForm.exclude_friends.join(','))
    
    if (isEditMode.value) {
      // 编辑模式：调用更新API
      await axios.put(`/api/corners/${currentEditCornerId.value}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      ElMessage.success('角落修改成功！')
    } else {
      // 新建模式：调用创建API
      await axios.post('/api/corners', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      ElMessage.success('角落分享成功！')
    }
    
    showShareDialog.value = false
    // 重置编辑模式
    isEditMode.value = false
    currentEditCornerId.value = null
    loadCorners() // 重新加载数据
    
  } catch (error) {
    ElMessage.error(`${isEditMode.value ? '修改' : '分享'}失败：` + (error.response?.data?.error || error.message))
  } finally {
    submitting.value = false
  }
}

// 当前选中角落的用户点赞状态
const isLiked = ref(false)
// 当前选中角落的用户收藏状态
const isFavorited = ref(false)
// 收藏操作加载状态
const favoriting = ref(false)

// 处理点赞/取消点赞
const handleLike = async () => {
  if (!currentUser.value || !selectedCorner.value) return
  
  try {
    liking.value = true
    const response = await fetch(`http://localhost:5200/api/corners/${selectedCorner.value.id}/like`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            user_id: currentUser.value.id
          })
        })
    
    if (!response.ok) throw new Error('操作失败')
    
    const data = await response.json()
    // 更新点赞数和liked_users数组
    if (selectedCorner.value) {
      selectedCorner.value.likes = data.likes
      selectedCorner.value.liked_users = data.liked_users || []
    }
    
    // 同时更新corners数组中的对应角落数据，确保liked_users数组也同步更新
    const cornerIndex = corners.value.findIndex(c => c.id === selectedCorner.value.id)
    if (cornerIndex !== -1) {
      corners.value[cornerIndex].likes = data.likes
      corners.value[cornerIndex].liked_users = data.liked_users || []
    }
    
    // 更新点赞状态
    isLiked.value = data.is_liked
    
    ElMessage.success(data.message)
  } catch (error) {
    ElMessage.error(error.message || '操作失败，请重试')
  } finally {
    liking.value = false
  }
}

// 加载角落详情时获取点赞和收藏状态
const loadCornerDetail = async (cornerId) => {
  if (!currentUser.value) return
  
  try {
    // 使用axios代替fetch，保持与其他API调用一致的风格
    const response = await axios.get(`/api/corners/${cornerId}`, {
      params: { user_id: currentUser.value.id }
    })
    
    // 更新点赞和收藏状态
    isLiked.value = response.data.is_liked
    isFavorited.value = response.data.is_favorited
    
    // 确保selectedCorner对象也更新为最新数据
    if (selectedCorner.value && selectedCorner.value.id === cornerId) {
      selectedCorner.value = response.data.corner
    }
    
  } catch (error) {
    console.error('获取角落状态失败:', error)
    ElMessage.error('获取互动状态失败，请刷新重试')
  }
}

// 处理收藏/取消收藏
const handleFavorite = async () => {
  if (!currentUser.value || !selectedCorner.value) return
  
  try {
    favoriting.value = true
    const response = await fetch(`http://localhost:5200/api/corners/${selectedCorner.value.id}/favorite`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            user_id: currentUser.value.id
          })
        })
    
    if (!response.ok) throw new Error('操作失败')
    
    const data = await response.json()
    // 更新收藏状态和favorited_users数组
    isFavorited.value = data.is_favorited
    
    // 更新selectedCorner中的favorited_users数组
    if (selectedCorner.value) {
      selectedCorner.value.favorited_users = data.favorited_users || []
    }
    
    // 更新corners数组中的对应项，确保favorited_users数组也同步更新
    const cornerIndex = corners.value.findIndex(c => c.id === selectedCorner.value.id)
    if (cornerIndex !== -1) {
      corners.value[cornerIndex].favorited_users = data.favorited_users || []
    }
    
    ElMessage.success(data.message)
  } catch (error) {
    ElMessage.error(error.message || '操作失败，请重试')
  } finally {
    favoriting.value = false
  }
}

// 提交评论
const submitComment = async () => {
  if (!currentUser.value || !selectedCorner.value || !commentText.value.trim()) return
  
  try {
    commenting.value = true
    const response = await fetch(`http://localhost:5200/api/corners/${selectedCorner.value.id}/comment`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            user_id: currentUser.value.id,
            content: commentText.value.trim()
          })
        })
    
    if (!response.ok) throw new Error('评论失败')
    
    const data = await response.json()
    // 更新评论列表
    if (!selectedCorner.value.comments) {
      selectedCorner.value.comments = []
    }
    selectedCorner.value.comments.push(data.comment)
    
    // 清空输入框
    commentText.value = ''
    
    ElMessage.success('评论发表成功')
  } catch (error) {
    ElMessage.error(error.message || '评论失败，请重试')
  } finally {
    commenting.value = false
  }
}

// 删除评论
const handleDeleteComment = async (cornerId, commentId) => {
  if (!currentUser.value) return
  
  try {
    const response = await fetch(`http://localhost:5200/api/corners/${cornerId}/comments/${commentId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        user_id: currentUser.value.id
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || '删除失败')
    }
    
    // 更新本地评论列表
    if (selectedCorner.value && selectedCorner.value.comments) {
      selectedCorner.value.comments = selectedCorner.value.comments.filter(
        comment => comment.id !== commentId
      )
    }
    
    ElMessage.success('评论删除成功')
  } catch (error) {
    console.error('删除评论失败:', error)
    ElMessage.error(error.message || '删除失败，请重试')
  }
}

// 格式化日期
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 编辑角落
const editCorner = (corner) => {
  console.log('编辑角落:', corner.title)
  // 设置为编辑模式
  isEditMode.value = true
  currentEditCornerId.value = corner.id

  // 确保tags是数组类型
  const tags = Array.isArray(corner.tags) ? corner.tags : []

  // 填充现有数据
  Object.assign(shareForm, {
    title: corner.title,
    description: corner.description,
    address: corner.address,
    tags: tags.join(','),
    latitude: corner.latitude,
    longitude: corner.longitude,
    image: null,
    visibility: corner.visibility || 'public',
    specific_friends: corner.specific_friends || [],
    exclude_friends: corner.exclude_friends || []
  })
  shareFormTags.value = tags
  // 根据visibility类型恢复selectedFriends
  if (corner.visibility === 'exclude_friends') {
    selectedFriends.value = corner.exclude_friends || []
  } else {
    selectedFriends.value = corner.specific_friends || []
  }
  imagePreview.value = corner.image_url
  showShareDialog.value = true
}

// 删除角落
const deleteCorner = async (cornerId) => {
  if (!currentUser.value) return
  
  try {
    const response = await axios.delete(`/api/corners/${cornerId}`, getAuthConfig())
    ElMessage.success('角落删除成功')
    // 重新加载数据
    loadCorners()
  } catch (error) {
    ElMessage.error('删除失败：' + (error.response?.data?.error || error.message))
  }
}

// 在地图上查看角落
const viewCornerOnMap = (corner) => {
  // 地图定位到角落位置
  map.value.setView([corner.latitude, corner.longitude], 16)
  
  // 找到对应的标记并打开弹窗
  const marker = markers.value.find(m => {
    const pos = m.getLatLng()
    return Math.abs(pos.lat - corner.latitude) < 0.0001 && Math.abs(pos.lng - corner.longitude) < 0.0001
  })
  
  if (marker) {
    marker.openPopup()
  }
  
  // 显示详情对话框
  selectedCorner.value = corner
  showCornerDetail.value = true
  
  // 先从corner数据中检查用户是否已点赞收藏（如果有liked_users和favorited_users字段）
  if (currentUser.value && corner.liked_users && corner.liked_users.includes(currentUser.value.id)) {
    isLiked.value = true
  } else {
    isLiked.value = false
  }
  
  if (currentUser.value && corner.favorited_users && corner.favorited_users.includes(currentUser.value.id)) {
    isFavorited.value = true
  } else {
    isFavorited.value = false
  }
  
  // 加载最新的点赞和收藏状态（确保数据同步）
  loadCornerDetail(corner.id)
}

// 定位用户当前位置
const locateUser = () => {
  if (!navigator.geolocation) {
    ElMessage.error('您的浏览器不支持地理定位功能')
    return
  }
  
  locating.value = true
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords
      
      // 移除之前的用户位置标记
       if (userLocationMarker.value) {
         map.value.removeLayer(userLocationMarker.value)
         // 清理脉冲标记和动画
         if (userLocationMarker.value.pulseMarker) {
           map.value.removeLayer(userLocationMarker.value.pulseMarker)
         }
         if (userLocationMarker.value.pulseAnimation) {
           clearInterval(userLocationMarker.value.pulseAnimation)
         }
       }
      
      // 创建用户位置标记 - 使用CircleMarker确保正确的地理定位
       userLocationMarker.value = L.circleMarker([latitude, longitude], {
         radius: 8,
         fillColor: '#409eff',
         color: '#ffffff',
         weight: 3,
         opacity: 1,
         fillOpacity: 0.8
       }).addTo(map.value)
         .bindPopup('您的当前位置')
       
       // 添加脉冲效果
       const pulseMarker = L.circleMarker([latitude, longitude], {
         radius: 8,
         fillColor: '#409eff',
         color: '#409eff',
         weight: 0,
         opacity: 0.6,
         fillOpacity: 0.1
       }).addTo(map.value)
       
       // 创建脉冲动画
       let currentRadius = 8
       const pulseAnimation = setInterval(() => {
         currentRadius += 2
         if (currentRadius > 20) {
           currentRadius = 8
         }
         pulseMarker.setRadius(currentRadius)
         pulseMarker.setStyle({
           opacity: 0.6 - (currentRadius - 8) / 20,
           fillOpacity: 0.1 - (currentRadius - 8) / 40
         })
       }, 100)
       
       // 保存动画引用以便清理
       userLocationMarker.value.pulseMarker = pulseMarker
       userLocationMarker.value.pulseAnimation = pulseAnimation
      
      // 地图定位到用户位置
      map.value.setView([latitude, longitude], 15)
      
      locating.value = false
      ElMessage.success('定位成功！')
    },
    (error) => {
      locating.value = false
      let errorMessage = '定位失败'
      
      switch(error.code) {
        case error.PERMISSION_DENIED:
          errorMessage = '用户拒绝了地理位置请求'
          break
        case error.POSITION_UNAVAILABLE:
          errorMessage = '位置信息不可用'
          break
        case error.TIMEOUT:
          errorMessage = '定位请求超时'
          break
        default:
          errorMessage = '定位时发生未知错误'
          break
      }
      
      ElMessage.error(errorMessage)
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000
    }
  )
}

// 生命周期
onMounted(() => {
  // 获取当前用户
  const userData = localStorage.getItem('currentUser')
  if (userData) {
    currentUser.value = JSON.parse(userData)
  }
  
  nextTick(() => {
    initMap()
    
    // 检查是否有需要查看的角落
    const viewCornerData = localStorage.getItem('viewCorner')
    if (viewCornerData) {
      try {
        const corner = JSON.parse(viewCornerData)
        // 定位到角落位置
        map.value.setView([corner.latitude, corner.longitude], 16)
        
        // 模拟点击角落标记
        selectedCorner.value = corner
        showCornerDetail.value = true
        
        // 清除localStorage中的标记
        localStorage.removeItem('viewCorner')
        
        console.log('已定位到角落:', corner.title)
      } catch (error) {
        console.error('解析角落数据失败:', error)
      }
    }
    
    // 更新我的角落和收藏
    updateMyCornersAndFavorites()
  })
})

onUnmounted(() => {
  // 清理待确认状态
  clearPendingLocation()
  
  if (map.value) {
    map.value.remove()
  }
})
</script>

<style scoped>
.map-page {
  display: flex;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.left-panel {
  width: 350px;
  background: white;
  border-right: 1px solid #ebeef5;
  overflow-y: auto;
  z-index: 1000;
}

.map-container {
  flex: 1;
  height: 100%;
}

.welcome-section {
  padding: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.brand-info {
  text-align: left;
}

.brand-info h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 1.5rem;
}

.brand-info p {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.user-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: white;
  font-weight: 600;
}

.username {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.user-dropdown .dropdown-trigger {
  padding: 4px;
  color: #909399;
  transition: color 0.3s;
}

.user-dropdown .dropdown-trigger:hover {
  color: #409eff;
}

.tip-section {
  margin-top: 12px;
}





.tip-section .el-alert {
  border-radius: 6px;
}

.recent-section {
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.corner-tabs {
  width: 100%;
  max-width: 300px;
}

/* 自定义标签页样式 */
.corner-tabs :deep(.el-tabs__nav) {
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.corner-tabs :deep(.el-tabs__item) {
  flex: 1;
  text-align: center;
  font-size: 14px;
  font-weight: 500;
  padding: 12px 0;
  border-radius: 8px 8px 0 0;
  transition: all 0.3s ease;
}

.corner-tabs :deep(.el-tabs__item:hover) {
  color: #409eff;
  background: rgba(64, 158, 255, 0.05);
}

.corner-tabs :deep(.el-tabs__item.is-active) {
  color: #409eff;
  font-weight: 600;
  background: rgba(64, 158, 255, 0.1);
}

.corner-tabs :deep(.el-tabs__active-bar) {
  background: #409eff;
  height: 3px;
  border-radius: 3px;
}

.tab-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  background: #409eff;
  color: white;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  vertical-align: middle;
  transform: translateY(-1px);
}

.corners-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: calc(100vh - 260px);
  overflow-y: auto;
}

.corner-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.corner-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.corner-main {
  display: flex;
  gap: 12px;
  cursor: pointer;
}

.corner-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px dashed #f0f0f0;
}

.corner-actions .el-button {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.corner-image {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  border-radius: 6px;
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
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.corner-content p {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.corner-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.map-controls {
  position: absolute;
  top: 80px;
  left: 370px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 搜索面板样式 */
.search-panel {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 15px;
}

.search-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}

.search-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  border-left: 3px solid #409eff;
  margin-bottom: 10px;
}

.search-info {
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.friends-only-toggle {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.friends-only-toggle .el-switch {
  --el-switch-on-color: #67c23a;
  --el-switch-off-color: #909399;
}

/* 内联定位按钮样式 */
.location-btn-inline {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #67c23a, #85ce61);
  border: none;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.location-btn-inline:hover {
  background: linear-gradient(135deg, #85ce61, #67c23a);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
  transform: translateY(-1px);
}

.location-btn-inline:active {
  transform: translateY(0);
}

.location-btn-inline .el-icon {
  color: white;
  font-size: 16px;
}

/* 保留原有control-panel样式以兼容其他可能的使用 */
.control-panel {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-input {
  width: 250px;
}

.tag-select {
  width: 200px;
}

.tag-tip {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}

.tags-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
}

.page-info {
  color: #606266;
  font-size: 12px;
  min-width: 60px;
  text-align: center;
}



.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  border: 2px dashed #dcdfe6;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.05);
}

.upload-icon {
  font-size: 28px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.image-preview {
  text-align: center;
}

.image-preview img {
  max-width: 100%;
  max-height: 120px;
  border-radius: 4px;
}

.location-info {
  color: #909399;
  font-size: 12px;
}

.corner-detail {
    .corner-image {
      text-align: center;
      margin-bottom: 16px;
    }
    
    .corner-image img {
      max-width: 100%;
      max-height: 200px;
      border-radius: 8px;
    }
    
    .corner-content {
      p {
        line-height: 1.6;
        margin-bottom: 16px;
      }
      
      .corner-meta {
        background: #f5f7fa;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 16px;
        p {
          margin: 4px 0;
          font-size: 14px;
        }
      }
      
      .corner-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
      }
      
      /* 互动操作区域样式 */
      .interaction-section {
        margin: 20px 0;
        display: flex;
        align-items: center;
        gap: 20px;
        .login-tip {
          margin-left: 10px;
          color: #909399;
          font-size: 14px;
        }
      }
      
      .interaction-button {
        margin-right: 10px;
      }
      
      /* 点赞按钮样式 */
      .like-button-wrapper {
        display: flex;
        align-items: center;
        gap: 8px;
        position: relative;
      }
      
      .like-button {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border: none;
        box-shadow: 0 2px 8px rgba(255, 102, 102, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        position: relative;
        cursor: pointer;
        
        /* 默认状态增强 */
        &::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
          transition: left 0.5s ease;
        }
        
        /* 悬停状态 */
        &:hover {
          transform: scale(1.1);
          box-shadow: 0 4px 12px rgba(255, 102, 102, 0.4);
          background: linear-gradient(135deg, #fcb69f 0%, #ffecd2 100%);
          &::before {
            left: 100%;
          }
        }
        
        /* 点击状态 */
        &:active {
          transform: scale(0.95);
          box-shadow: 0 2px 4px rgba(255, 102, 102, 0.3);
        }
        
        /* 禁用状态 */
        &:disabled {
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          box-shadow: none;
          cursor: not-allowed;
          transform: none;
          opacity: 0.7;
        }
        
        /* 激活状态（已点赞） */
        &.liked {
          background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
          box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4);
          animation: likePop 0.3s ease-out;
          
          /* 激活状态粒子效果 */
          &::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            animation: particleEffect 0.6s ease-out;
          }
        }
        
        /* 加载状态增强 */
        &:loading {
          background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 50%, #ffecd2 100%);
          background-size: 200% 100%;
          animation: loadingShine 1.5s infinite;
        }
      }
      
      /* 点赞数样式 */
      .like-count {
        font-size: 16px;
        font-weight: 600;
        color: #606266;
        transition: all 0.3s ease;
        min-width: 24px;
        text-align: center;
      }
      
      .like-count-active {
        color: #ff6b6b;
        animation: likeCountChange 0.5s ease;
      }
      
      /* 点赞动画 */
      @keyframes likePop {
        0% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.2);
        }
        100% {
          transform: scale(1);
        }
      }
      
      @keyframes likeCountChange {
        0% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.3);
        }
        100% {
          transform: scale(1);
        }
      }
      
      /* 收藏按钮样式 */
      .favorite-button-wrapper {
        display: flex;
        align-items: center;
        gap: 8px;
        position: relative;
      }
      
      .favorite-button {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #e0f7fa 0%, #80deea 100%);
        border: none;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        position: relative;
        cursor: pointer;
        
        /* 默认状态增强 */
        &::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
          transition: left 0.5s ease;
        }
        
        /* 悬停状态 */
        &:hover {
          transform: scale(1.1);
          box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
          background: linear-gradient(135deg, #80deea 0%, #e0f7fa 100%);
          &::before {
            left: 100%;
          }
        }
        
        /* 点击状态 */
        &:active {
          transform: scale(0.95);
          box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
        }
        
        /* 禁用状态 */
        &:disabled {
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          box-shadow: none;
          cursor: not-allowed;
          transform: none;
          opacity: 0.7;
        }
        
        /* 激活状态（已收藏） */
        &.favorited {
          background: linear-gradient(135deg, #409eff 0%, #36cfc9 100%);
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
          animation: favoritePop 0.3s ease-out;
          
          /* 激活状态粒子效果 */
          &::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            animation: particleEffect 0.6s ease-out;
          }
        }
        
        /* 加载状态增强 */
        &:loading {
          background: linear-gradient(135deg, #e0f7fa 0%, #80deea 50%, #e0f7fa 100%);
          background-size: 200% 100%;
          animation: loadingShine 1.5s infinite;
        }
      }
      
      /* 收藏文本样式 */
      .favorite-text {
        font-size: 16px;
        font-weight: 600;
        color: #606266;
        transition: all 0.3s ease;
      }
      
      .favorite-text-active {
        color: #409eff;
        animation: favoriteTextChange 0.5s ease;
      }
      
      /* 收藏动画 */
      @keyframes favoritePop {
        0% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.2) rotate(10deg);
        }
        100% {
          transform: scale(1) rotate(0);
        }
      }
      
      @keyframes favoriteTextChange {
        0% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.2);
        }
        100% {
          transform: scale(1);
        }
      }
      
      /* 粒子效果动画 */
      @keyframes particleEffect {
        0% {
          width: 0;
          height: 0;
          opacity: 0.8;
        }
        100% {
          width: 100px;
          height: 100px;
          opacity: 0;
        }
      }
      
      /* 加载闪光动画 */
      @keyframes loadingShine {
        0% {
          background-position: 200% 0;
        }
        100% {
          background-position: -200% 0;
        }
      }
      
      /* 图标状态样式 */
      .el-icon {
        font-size: 18px;
        transition: all 0.3s ease;
      }
      
      .like-button .el-icon {
        color: #606266;
      }
      
      .like-button.liked .el-icon {
        color: white;
        animation: iconBounce 0.3s ease;
      }
      
      .favorite-button .el-icon {
        color: #606266;
      }
      
      .favorite-button.favorited .el-icon {
        color: white;
        animation: iconBounce 0.3s ease;
      }
      
      /* 图标弹跳动画 */
      @keyframes iconBounce {
        0%, 100% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.3) rotate(15deg);
        }
      }
      
      /* 评论区域样式 */
      .comments-section {
          margin-top: 24px;
          
          h4 {
            margin-bottom: 16px;
            color: #303133;
            font-weight: 600;
            font-size: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #f0f0f0;
          }
          
          .comment-input-section {
            margin-bottom: 24px;
            padding: 16px;
            background: #fafafa;
            border-radius: 8px;
            
            .comment-actions {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-top: 10px;
              
              .comment-tip {
                font-size: 12px;
                color: #909399;
              }
            }
          }
          
          .login-to-comment {
            text-align: center;
            padding: 30px 0;
            margin-bottom: 24px;
            background: #fafafa;
            border-radius: 8px;
          }
          
          .comments-list {
            
            .comment-item {
              padding: 16px 0;
              border-bottom: 1px solid #f5f7fa;
              transition: background-color 0.3s;
              
              &:hover {
                background-color: rgba(0, 0, 0, 0.01);
              }
              
              &:last-child {
                border-bottom: none;
              }
              
              .comment-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
                
                .comment-main {
                  display: flex;
                  align-items: center;
                }
                
                .comment-info {
                  margin-left: 10px;
                  display: flex;
                  flex-direction: column;
                }
                
                .comment-username {
                  font-size: 14px;
                  font-weight: 600;
                  color: #303133;
                }
                
                .comment-time {
                  font-size: 12px;
                  color: #909399;
                  margin-top: 2px;
                }
              }
              
              .delete-button {
                color: #ff4d4f;
                padding: 0;
                font-size: 12px;
                opacity: 0.8;
                
                &:hover {
                  color: #ff7875;
                  opacity: 1;
                }
              }
              
              .comment-content {
                font-size: 14px;
                line-height: 1.7;
                color: #606266;
                padding-left: 34px;
                word-break: break-word;
                white-space: pre-wrap;
              }
            }
          }
          
          .no-comments {
            padding: 40px 0;
            text-align: center;
            color: #909399;
          }
        }
    }
  }

/* 响应式设计 */
@media (max-width: 768px) {
  .map-page {
    flex-direction: column;
    height: calc(100vh - 60px);
  }
  
  .left-panel {
    width: 100%;
    height: 180px;
    border-right: none;
    border-bottom: 1px solid #ebeef5;
  }
  
  .welcome-section {
    padding: 16px;
  }
  
  .welcome-section h2 {
    font-size: 1.25rem;
  }
  
  .header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .brand-info {
    text-align: left;
  }
  
  .brand-info h2 {
    font-size: 1.3rem;
  }
  
  .user-status {
    align-self: flex-end;
  }
  
  .username {
    display: none;
  }
  
  .recent-section {
    padding: 16px;
  }
  
  .corners-list {
    flex-direction: row;
    overflow-x: auto;
    max-height: none;
    padding-bottom: 8px;
  }
  
  .corner-item {
    flex-shrink: 0;
    width: 200px;
  }
  
  .map-container {
    flex: 1;
    height: 60vh;
  }
  
  .map-controls {
    left: 10px;
    right: 10px;
    top: 70px;
    width: calc(100% - 20px);
    max-width: none;
  }
  
  .search-panel {
    padding: 12px;
  }
  
  .search-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .search-input {
    width: 100%;
  }
  
  .tag-select {
    width: 100%;
  }
  
  .search-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .location-btn-inline {
    width: 36px;
    height: 36px;
  }
  
  .location-btn-inline .el-icon {
    font-size: 14px;
  }
  
  /* 保留原有响应式样式 */
  .control-panel {
    flex-direction: column;
    align-items: stretch;
  }
}


</style>

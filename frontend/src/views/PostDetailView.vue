<template>
  <div class="post-detail-view">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading...</p>
    </div>

    <div v-else-if="post" class="post-detail-container">
      <!-- Header -->
      <div class="detail-header">
        <button @click="goBack" class="back-btn">
          <span class="back-icon">←</span>
          <span>Back</span>
        </button>
        <h1>{{ post.title }}</h1>
      </div>

      <!-- Post Info -->
      <div class="post-info">
        <div class="user-info">
          <div class="avatar">{{ username.charAt(0).toUpperCase() }}</div>
          <div class="user-details">
            <span class="username">{{ username }}</span>
            <span class="timestamp">{{ formattedTime }}</span>
          </div>
        </div>
        <button 
          v-if="isOwner" 
          @click="handleDelete" 
          class="delete-btn"
          :disabled="deleting"
        >
          {{ deleting ? 'Deleting...' : 'Delete' }}
        </button>
      </div>

      <!-- Description -->
      <p v-if="post.description" class="description">{{ post.description }}</p>

      <!-- Tags -->
      <div v-if="post.tags && post.tags.length > 0" class="tags">
        <span v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</span>
      </div>

      <!-- Corners / Route -->
      <div v-if="post.corners && post.corners.length > 0" class="locations-section">
        <!-- Single corner -->
        <template v-if="post.corners.length === 1">
          <h3>Location</h3>
          <div class="corner-list">
            <div 
              v-for="corner in post.corners" 
              :key="corner._id" 
              class="corner-item"
              @click="goToMap(corner)"
            >
              <span class="corner-icon">📍</span>
              <span class="corner-name">{{ corner.name }}</span>
            </div>
          </div>
        </template>
        
        <!-- Multiple corners as route -->
        <template v-else>
          <div class="route-header">
            <h3>🛤️ Route</h3>
            <button @click="showRouteOnMap" class="view-route-btn">View on Map</button>
          </div>
          <div class="route-stops">
            <div 
              v-for="(corner, idx) in getOrderedCorners()" 
              :key="corner._id" 
              class="route-stop"
              @click="goToMap(corner)"
            >
              <span class="stop-number">{{ idx + 1 }}</span>
              <span class="stop-name">{{ corner.name }}</span>
              <span v-if="idx < getOrderedCorners().length - 1" class="stop-arrow">↓</span>
            </div>
          </div>
        </template>
      </div>

      <!-- Media Gallery -->
      <div class="media-gallery">
        <h3>Media ({{ post.media_files.length }})</h3>
        <div class="media-grid">
          <div
            v-for="(fileId, idx) in post.media_files"
            :key="idx"
            class="media-item"
            @click="openMediaViewer(idx)"
          >
            <img
              v-if="post.media_type === 'image'"
              :src="getMediaUrl(fileId)"
              :alt="`Media ${idx + 1}`"
            />
            <video
              v-else
              :src="getMediaUrl(fileId)"
              preload="metadata"
            />
            <div v-if="post.media_type === 'video'" class="video-indicator">▶</div>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats">
        <span class="stat">❤️ {{ likeCount }} likes</span>
        <span class="stat">💬 {{ commentCount }} comments</span>
        <span class="stat">⭐ {{ favoriteCount }} favorites</span>
      </div>

      <!-- Comments -->
      <div class="comments-section">
        <h3>Comments</h3>
        <CommentForm :post-id="post._id" @comment-added="handleCommentAdded" />
        <CommentList 
          :post-id="post._id" 
          @comment-deleted="handleCommentDeleted"
          @comment-count-changed="handleCommentCountChanged"
        />
      </div>
    </div>

    <!-- Media Viewer Modal -->
    <div v-if="showMediaViewer" class="media-viewer-modal" @click.self="closeMediaViewer">
      <div class="media-viewer-content">
        <button @click="closeMediaViewer" class="close-btn">×</button>
        <button v-if="currentMediaIndex > 0" @click="prevMedia" class="nav-btn prev">←</button>
        
        <div class="media-display">
          <img
            v-if="post.media_type === 'image'"
            :src="getMediaUrl(post.media_files[currentMediaIndex])"
            :alt="`Media ${currentMediaIndex + 1}`"
          />
          <video
            v-else
            :src="getMediaUrl(post.media_files[currentMediaIndex])"
            controls
            autoplay
          />
        </div>

        <button 
          v-if="currentMediaIndex < post.media_files.length - 1" 
          @click="nextMedia" 
          class="nav-btn next"
        >
          →
        </button>
        
        <div class="media-counter">
          {{ currentMediaIndex + 1 }} / {{ post.media_files.length }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { postsApi } from '../api/posts';
import { likesApi } from '../api/likes';
import { favoritesApi } from '../api/favorites';
import { mediaApi } from '../api/media';
import { useAuth } from '../composables/useAuth';
import { formatters } from '../utils/format';
import CommentForm from '../components/Feed/CommentForm.vue';
import CommentList from '../components/Feed/CommentList.vue';

const router = useRouter();
const route = useRoute();
const { user: currentUser } = useAuth();

const post = ref(null);
const loading = ref(true);
const showMediaViewer = ref(false);
const currentMediaIndex = ref(0);
const likeCount = ref(0);
const commentCount = ref(0);
const favoriteCount = ref(0);
const deleting = ref(false);

const username = computed(() => post.value?.username || 'Unknown User');
const formattedTime = computed(() => formatters.formatRelativeTime(post.value?.created_at));
const isOwner = computed(() => currentUser.value?.id === post.value?.user_id);

const loadPost = async () => {
  const postId = route.params.postId;
  loading.value = true;

  try {
    const response = await postsApi.get(postId);
    if (response.success && response.data) {
      post.value = response.data;
      likeCount.value = response.data.stats?.likes_count || 0;
      commentCount.value = response.data.stats?.comments_count || 0;
      favoriteCount.value = response.data.stats?.favorites_count || 0;
    }
  } catch (err) {
    console.error('Failed to load post:', err);
    router.back();
  } finally {
    loading.value = false;
  }
};

const getMediaUrl = (fileId) => {
  return mediaApi.getUrl(fileId);
};

const goBack = () => {
  router.back();
};

const goToMap = (corner) => {
  router.push({
    path: '/map',
    query: {
      corner_id: corner._id,
      lat: corner.location?.coordinates[1],
      lng: corner.location?.coordinates[0]
    }
  });
};

// Get ordered corners (use route order if available)
const getOrderedCorners = () => {
  if (!post.value?.corners || post.value.corners.length === 0) {
    return [];
  }
  
  // If route exists with corner_ids, order by that
  if (post.value.route?.corner_ids && post.value.route.corner_ids.length > 0) {
    return post.value.route.corner_ids
      .map(cornerId => post.value.corners.find(c => c._id === cornerId))
      .filter(Boolean);
  }
  
  // Otherwise use corners in their original order
  return post.value.corners;
};

const showRouteOnMap = () => {
  const orderedCorners = getOrderedCorners();
  
  if (orderedCorners.length < 2) {
    return;
  }

  // Store route data in session storage
  sessionStorage.setItem('route_data', JSON.stringify({
    route_name: post.value.route?.route_name || `Route (${orderedCorners.length} stops)`,
    corners: orderedCorners
  }));

  // Navigate to map
  router.push({
    path: '/map',
    query: {
      show_route: 'true',
      center_lat: orderedCorners[0].location?.coordinates[1],
      center_lng: orderedCorners[0].location?.coordinates[0]
    }
  });
};

const openMediaViewer = (index) => {
  currentMediaIndex.value = index;
  showMediaViewer.value = true;
};

const closeMediaViewer = () => {
  showMediaViewer.value = false;
  currentMediaIndex.value = 0;
};

const prevMedia = () => {
  if (currentMediaIndex.value > 0) {
    currentMediaIndex.value--;
  }
};

const nextMedia = () => {
  if (currentMediaIndex.value < post.value.media_files.length - 1) {
    currentMediaIndex.value++;
  }
};

const handleDelete = async () => {
  if (!confirm('确定要删除这个帖子吗？')) return;

  deleting.value = true;
  try {
    await postsApi.delete(post.value._id);
    router.back();
  } catch (err) {
    alert('删除失败');
  } finally {
    deleting.value = false;
  }
};

const handleCommentAdded = () => {
  commentCount.value++;
};

const handleCommentDeleted = () => {
  commentCount.value--;
};

const handleCommentCountChanged = (count) => {
  commentCount.value = count;
};

onMounted(() => {
  loadPost();
});
</script>

<style scoped>
.post-detail-view {
  height: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.post-detail-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f5f5f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  color: #666;
}

.back-btn:hover {
  background: #e0e0e0;
  color: #333;
}

.back-icon {
  font-size: 18px;
}

.detail-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.post-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 16px;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.username {
  font-weight: 600;
  color: #333;
  font-size: 15px;
}

.timestamp {
  font-size: 12px;
  color: #999;
}

.delete-btn {
  padding: 8px 16px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.delete-btn:hover:not(:disabled) {
  background: #ff5252;
}

.delete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.description {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
  font-size: 15px;
}

.tags {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 6px 14px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 16px;
  font-size: 14px;
}

.locations-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.locations-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.corner-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.corner-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.corner-item:hover {
  background: #e0e0e0;
}

.corner-icon {
  font-size: 18px;
}

.corner-name {
  font-size: 14px;
  color: #333;
}

.route-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.route-header h3 {
  margin: 0;
}

.view-route-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.view-route-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.route-stops {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.route-stop {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.route-stop:hover {
  background: #e3f2fd;
}

.stop-number {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.stop-name {
  flex: 1;
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.stop-arrow {
  color: #667eea;
  font-size: 16px;
}

.media-gallery {
  margin-bottom: 24px;
}

.media-gallery h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.media-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #f0f0f0;
}

.media-item img,
.media-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48px;
  color: white;
  background: rgba(0, 0, 0, 0.5);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats {
  display: flex;
  gap: 24px;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
  margin-bottom: 24px;
}

.stat {
  font-size: 14px;
  color: #666;
}

.comments-section {
  border-top: 1px solid #f0f0f0;
  padding-top: 24px;
}

.comments-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

/* Media Viewer Modal */
.media-viewer-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.media-viewer-content {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn {
  position: fixed;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  font-size: 28px;
  color: #333;
  cursor: pointer;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  z-index: 10;
  transition: all 0.3s;
}

.close-btn:hover {
  background: white;
  transform: scale(1.1);
}

.nav-btn {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  border: none;
  font-size: 24px;
  color: #333;
  cursor: pointer;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  z-index: 10;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-btn:hover {
  background: #409eff;
  color: white;
  transform: translateY(-50%) scale(1.1);
}

.nav-btn.prev {
  left: 10px;
}

.nav-btn.next {
  right: 10px;
}

.media-display {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 60px;
  box-sizing: border-box;
}

.media-display img,
.media-display video {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.media-counter {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.9);
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  color: #666;
  z-index: 10;
}

/* Responsive for small screens */
@media (max-width: 480px) {
  .nav-btn {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .nav-btn.prev {
    left: 5px;
  }
  
  .nav-btn.next {
    right: 5px;
  }
  
  .media-display {
    padding: 50px 50px;
  }
}
</style>
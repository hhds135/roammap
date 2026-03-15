<template>
  <div :class="['post-card', { compact: compact }]">
    <div class="post-header">
      <div class="user-info" @click="goToProfile">
        <div class="avatar">{{ username.charAt(0).toUpperCase() }}</div>
        <div class="user-details">
          <span class="username">{{ username }}</span>
          <span class="timestamp">{{ formattedTime }}</span>
        </div>
      </div>
      <button 
        v-if="isOwner" 
        @click="handleDelete" 
        class="delete-post-btn"
        :disabled="deleting"
      >
        {{ deleting ? 'Deleting...' : 'Delete' }}
      </button>
    </div>

    <h3 class="post-title">{{ post.title }}</h3>
    <p v-if="post.description" class="post-description">{{ post.description }}</p>

    <!-- Media Content -->
    <div class="post-media" @click="goToDetail">
      <template v-if="post.media_type === 'image'">
        <img
          v-for="(fileId, idx) in post.media_files"
          :key="idx"
          :src="getMediaUrl(fileId)"
          :alt="`post-${idx}`"
          loading="lazy"
        />
      </template>
      <template v-else-if="post.media_type === 'video'">
        <video
          v-for="(fileId, idx) in post.media_files"
          :key="idx"
          :src="getMediaUrl(fileId)"
          controls
          preload="metadata"
        />
      </template>
    </div>

    <!-- Location Tags / Route -->
    <div v-if="post.corners && post.corners.length > 0" class="post-locations">
      <!-- Single corner: show as tag -->
      <template v-if="post.corners.length === 1">
        <span 
          v-for="corner in post.corners" 
          :key="corner._id" 
          class="corner-tag"
          @click="handleCornerClick(corner)"
        >
          @{{ corner.name }}
        </span>
      </template>
      
      <!-- Multiple corners: show as route -->
      <template v-else>
        <div class="post-route" @click="handleRouteClick">
          <div class="route-header">
            <span class="route-icon">🛤️</span>
            <span class="route-title">{{ getRouteTitle() }}</span>
          </div>
          <div class="route-stops">
            <div 
              v-for="(corner, idx) in getOrderedCorners()" 
              :key="corner._id" 
              class="route-stop"
              @click.stop="handleCornerClick(corner)"
            >
              <span class="stop-number">{{ idx + 1 }}</span>
              <span class="stop-name">{{ corner.name }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Tags -->
    <div v-if="post.tags && post.tags.length > 0" class="post-tags">
      <span v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</span>
    </div>

    <!-- Stats -->
    <div class="post-stats">
      <button 
        @click="handleLike" 
        :class="['stat-button', { liked: isLiked }]"
        :disabled="loadingLike"
      >
        <span class="stat-icon">{{ isLiked ? '❤️' : '👍' }}</span>
        <span class="stat-number">{{ likeCount }}</span>
      </button>
      <button 
        @click="toggleComments" 
        :class="['stat-button', { active: showComments }]"
      >
        <span class="stat-icon">💬</span>
        <span class="stat-number">{{ commentCount }}</span>
      </button>
      <button 
        @click="handleFavorite" 
        :class="['stat-button', { favorited: isFavorited }]"
        :disabled="loadingFavorite"
      >
        <span class="stat-icon">⭐</span>
        <span class="stat-number">{{ favoriteCount }}</span>
      </button>
      <button 
        @click="handleShare" 
        class="stat-button"
        title="Share"
      >
        <span class="stat-icon">🔗</span>
      </button>
    </div>

    <!-- Comments Section -->
    <div v-if="showComments" class="comments-section">
      <CommentForm 
        :post-id="post._id" 
        @comment-added="handleCommentAdded"
      />
      <CommentList 
        ref="commentListRef"
        :post-id="post._id" 
        @comment-deleted="handleCommentDeleted"
        @comment-count-changed="handleCommentCountChanged"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { mediaApi } from '../../api/media';
import { likesApi } from '../../api/likes';
import { favoritesApi } from '../../api/favorites';
import { postsApi } from '../../api/posts';
import { formatters } from '../../utils/format';
import { useAuth } from '../../composables/useAuth';
import CommentList from './CommentList.vue';
import CommentForm from './CommentForm.vue';

const router = useRouter();
const props = defineProps({
  post: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['view']);

const { user: currentUser } = useAuth();
const isLiked = ref(false);
const likeCount = ref(0);
const loadingLike = ref(false);
const showComments = ref(false);
const commentCount = ref(0);
const commentListRef = ref(null);
const isFavorited = ref(false);
const favoriteCount = ref(0);
const loadingFavorite = ref(false);
const deleting = ref(false);

const isOwner = computed(() => {
  return currentUser.value && currentUser.value.id === props.post.user_id;
});

const username = computed(() => props.post.username || 'Unknown User');

const formattedTime = computed(() => {
  return formatters.formatRelativeTime(props.post.created_at);
});

const getMediaUrl = (fileId) => {
  return mediaApi.getUrl(fileId);
};

const goToDetail = () => {
  router.push({
    path: `/post/${props.post._id}`
  });
};

const goToProfile = () => {
  if (props.post.user_id) {
    router.push({
      path: `/profile/${props.post.user_id}`
    });
  }
};

// Handle like/unlike
const handleLike = async () => {
  if (!currentUser.value || loadingLike.value) return;
  
  loadingLike.value = true;
  try {
    const response = await likesApi.toggle(props.post._id);
    if (response.success && response.data) {
      isLiked.value = response.data.is_liked;
      likeCount.value = response.data.likes_count;
    }
  } catch (err) {
    console.error('Failed to toggle like:', err);
  } finally {
    loadingLike.value = false;
  }
};

// Handle favorite/unfavorite
const handleFavorite = async () => {
  if (!currentUser.value || loadingFavorite.value) return;
  
  loadingFavorite.value = true;
  try {
    const response = await favoritesApi.toggle(props.post._id);
    if (response.success && response.data) {
      isFavorited.value = response.data.is_favorited;
      favoriteCount.value = response.data.favorites_count;
    }
  } catch (err) {
    console.error('Failed to toggle favorite:', err);
  } finally {
    loadingFavorite.value = false;
  }
};

// Handle delete post
const handleDelete = async () => {
  if (!confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
    return;
  }

  deleting.value = true;
  try {
    const response = await postsApi.delete(props.post._id);
    if (response.success) {
      emit('deleted', props.post._id);
    } else {
      alert('Delete failed: ' + (response.error || 'Unknown error'));
    }
  } catch (err) {
    console.error('Failed to delete post:', err);
    alert('Delete failed: ' + (err.error?.message || 'Unknown error'));
  } finally {
    deleting.value = false;
  }
};

// Handle share
const handleShare = async () => {
  const shareUrl = `${window.location.origin}/post/${props.post._id}`;
  
  try {
    await navigator.clipboard.writeText(shareUrl);
    alert('链接已复制到剪贴板！');
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = shareUrl;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      alert('链接已复制到剪贴板！');
    } catch (e) {
      console.error('Failed to copy link:', e);
      alert('复制链接失败，请手动复制');
    }
    document.body.removeChild(textArea);
  }
};

// Handle corner click - navigate to map and highlight corner
const handleCornerClick = (corner) => {
  // Navigate to map with corner info
  router.push({
    path: '/map',
    query: {
      corner_id: corner._id,
      lat: corner.location?.coordinates[1],
      lng: corner.location?.coordinates[0]
    }
  });
};

// Get route title
const getRouteTitle = () => {
  if (props.post.route?.route_name) {
    return props.post.route.route_name;
  }
  return `Route (${props.post.corners?.length || 0} stops)`;
};

// Get ordered corners (use route order if available, otherwise use corners order)
const getOrderedCorners = () => {
  if (!props.post.corners || props.post.corners.length === 0) {
    return [];
  }
  
  // If route exists with corner_ids, order by that
  if (props.post.route?.corner_ids && props.post.route.corner_ids.length > 0) {
    return props.post.route.corner_ids
      .map(cornerId => props.post.corners.find(c => c._id === cornerId))
      .filter(Boolean);
  }
  
  // Otherwise use corners in their original order
  return props.post.corners;
};

// Handle route click - navigate to map and show route
const handleRouteClick = () => {
  const orderedCorners = getOrderedCorners();
  
  if (orderedCorners.length < 2) {
    return;
  }

  // Store route data in session storage with proper format
  sessionStorage.setItem('route_data', JSON.stringify({
    route_name: getRouteTitle(),
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

// Toggle comments visibility
const toggleComments = () => {
  showComments.value = !showComments.value;
};

// Handle comment added
const handleCommentAdded = (comment) => {
  // Auto-open comments section if not already open
  if (!showComments.value) {
    showComments.value = true;
  }
  
  if (commentListRef.value) {
    commentListRef.value.addComment(comment);
  }
};

// Handle comment deleted
const handleCommentDeleted = () => {
  // Refresh comment list if needed
};

// Handle comment count changed
const handleCommentCountChanged = (count) => {
  commentCount.value = count;
};

// Initialize like status, comment count and favorite count
onMounted(() => {
  likeCount.value = props.post.stats?.likes_count || 0;
  commentCount.value = props.post.stats?.comments_count || 0;
  favoriteCount.value = props.post.stats?.favorites_count || 0;
  // Note: We could also fetch the like/favorite status if needed
  // For now, we'll just track them locally
});
</script>

<style scoped>
.post-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.post-header {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.user-info:hover {
  opacity: 0.7;
}

.delete-post-btn {
  padding: 6px 14px;
  background: #fee;
  color: #f56c6c;
  border: 1px solid #fcc;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.delete-post-btn:hover:not(:disabled) {
  background: #fec;
  border-color: #f99;
}

.delete-post-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
}

.username {
  font-weight: 600;
  color: #333;
}

.timestamp {
  font-size: 12px;
  color: #999;
}

.post-title {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #333;
}

.post-description {
  margin: 0 0 16px 0;
  color: #666;
  line-height: 1.6;
}

.post-media {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.post-media img,
.post-media video {
  width: 100%;
  display: block;
}

/* Compact mode styles */
.post-card.compact .post-media {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
  grid-auto-rows: 80px;
  margin-bottom: 12px;
}

.post-card.compact .post-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  aspect-ratio: 1;
}

.post-card.compact .post-media video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  aspect-ratio: 1;
}

.post-card.compact .post-header {
  padding: 12px 16px;
  margin-bottom: 0;
}

.post-card.compact .avatar {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.post-card.compact .user-details {
  gap: 2px;
}

.post-card.compact .username {
  font-size: 14px;
}

.post-card.compact .timestamp {
  font-size: 11px;
}

.post-card.compact .post-title {
  padding: 0 16px;
  font-size: 15px;
  margin-bottom: 8px;
}

.post-card.compact .post-description {
  padding: 0 16px;
  font-size: 13px;
  margin-bottom: 8px;
}

.post-card.compact .post-locations,
.post-card.compact .post-tags {
  padding: 0 16px;
  margin-bottom: 8px;
}

.post-card.compact .post-route {
  padding: 8px;
}

.post-card.compact .route-header {
  margin-bottom: 6px;
}

.post-card.compact .route-title {
  font-size: 14px;
}

.post-card.compact .route-stop {
  padding: 4px 8px;
}

.post-card.compact .stop-number {
  width: 20px;
  height: 20px;
  font-size: 11px;
}

.post-card.compact .stop-name {
  font-size: 13px;
}

.post-card.compact .post-stats {
  padding: 8px 16px;
  gap: 16px;
}

.post-card.compact .stat-button {
  padding: 6px 10px;
  font-size: 13px;
}

.post-card.compact .stat-icon {
  font-size: 16px;
}

.post-locations {
  margin-bottom: 12px;
}

.corner-tag {
  display: inline-block;
  padding: 4px 12px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 16px;
  font-size: 14px;
  margin-right: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.corner-tag:hover {
  background: #1976d2;
  color: white;
  transform: translateY(-1px);
}

.post-route {
  padding: 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid #dee2e6;
  cursor: pointer;
  transition: all 0.3s;
}

.post-route:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.route-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.route-icon {
  font-size: 18px;
}

.route-title {
  font-weight: 600;
  font-size: 15px;
  color: #333;
}

.route-stops {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.route-stop {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: white;
  border-radius: 8px;
  transition: all 0.2s;
}

.route-stop:hover {
  background: #e3f2fd;
}

.stop-number {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.stop-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.post-stats {
  display: flex;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.stat {
  font-size: 14px;
  color: #666;
}

.stat-button {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 20px;
  transition: all 0.3s;
  font-size: 14px;
}

.stat-button:hover:not(:disabled) {
  background: #f0f0f0;
}

.stat-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.stat-button.liked {
  color: #ff6b6b;
  background: #fef0f0;
}

.stat-button.liked:hover:not(:disabled) {
  background: #ffe0e0;
}

.stat-button.active {
  color: #667eea;
  background: #f0f4ff;
}

.stat-button.active:hover:not(:disabled) {
  background: #e3edff;
}

.stat-button.favorited {
  color: #ffc107;
  background: #fff8e1;
}

.stat-button.favorited:hover:not(:disabled) {
  background: #ffecb3;
}

.stat-icon {
  font-size: 18px;
  transition: transform 0.3s;
}

.stat-button:active:not(:disabled) .stat-icon {
  transform: scale(1.2);
}

.stat-number {
  font-weight: 600;
}

.comments-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
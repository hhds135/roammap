<template>
  <div class="feed-view">
    <div class="feed-container">
      <!-- Feed Type Toggle -->
      <div class="feed-toggle">
        <button
          :class="['toggle-button', { active: currentFeedType === 'following' }]"
          @click="switchFeed('following')"
        >
          <span class="toggle-icon">👥</span>
          <span>Following</span>
        </button>
        <button
          :class="['toggle-button', { active: currentFeedType === 'finding' }]"
          @click="switchFeed('finding')"
        >
          <span class="toggle-icon">📍</span>
          <span>Finding</span>
        </button>
        <button
          :class="['toggle-button', { active: currentFeedType === 'recommendation' }]"
          @click="switchFeed('recommendation')"
        >
          <span class="toggle-icon">✨</span>
          <span>Recommended</span>
        </button>
      </div>

      <!-- Finding Content -->
      <div v-if="currentFeedType === 'finding'" class="finding-section">
        <!-- Search Bar -->
        <div class="search-section">
          <div class="search-input-wrapper">
            <span class="search-icon">🔍</span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search places..."
              @keyup.enter="searchCorners"
            />
            <button v-if="searchQuery" @click="clearSearch" class="clear-search">×</button>
          </div>
          <button @click="searchCorners" class="search-btn">Search</button>
        </div>

        <!-- Search Results -->
        <div v-if="showSearchResults" class="search-results">
          <div class="section-header">
            <h3>Search Results</h3>
            <button @click="clearSearch" class="back-btn">Back to Hot</button>
          </div>
          
          <div v-if="searchLoading" class="loading">
            <div class="spinner"></div>
            <p>Searching...</p>
          </div>
          
          <div v-else-if="searchResults.length === 0" class="empty-state">
            <p>No places found</p>
          </div>
          
          <div v-else class="corners-list">
            <div
              v-for="corner in searchResults"
              :key="corner._id"
              class="corner-card"
              @click="goToCorner(corner)"
            >
              <div class="corner-image">
                <img v-if="corner.images && corner.images.length > 0" 
                     :src="getMediaUrl(corner.images[0])" 
                     :alt="corner.name" />
                <div v-else class="placeholder-image">📍</div>
              </div>
              <div class="corner-content">
                <h4 class="corner-name">{{ corner.name }}</h4>
                <p v-if="corner.description" class="corner-desc">{{ corner.description }}</p>
                <div class="corner-meta">
                  <span v-if="corner.distance" class="distance">
                    📍 {{ formatDistance(corner.distance) }}
                  </span>
                  <span v-if="corner.tags && corner.tags.length > 0" class="tags">
                    {{ corner.tags.slice(0, 2).join(', ') }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Hot Corners List -->
        <div v-else class="hot-corners-section">
          <div class="section-header">
            <h3>🔥 Hot Places</h3>
            <span class="subtitle">Popular places near you</span>
          </div>

          <div v-if="hotLoading" class="loading">
            <div class="spinner"></div>
            <p>Loading hot places...</p>
          </div>

          <div v-else-if="hotCorners.length === 0" class="empty-state">
            <p>No popular places found nearby</p>
          </div>

          <div v-else class="corners-list">
            <div
              v-for="(corner, index) in hotCorners"
              :key="corner._id"
              class="corner-card"
              @click="goToCorner(corner)"
            >
              <div class="rank-badge" :class="getRankClass(index)">{{ index + 1 }}</div>
              <div class="corner-image">
                <img v-if="corner.images && corner.images.length > 0" 
                     :src="getMediaUrl(corner.images[0])" 
                     :alt="corner.name" />
                <div v-else class="placeholder-image">📍</div>
              </div>
              <div class="corner-content">
                <h4 class="corner-name">{{ corner.name }}</h4>
                <p v-if="corner.description" class="corner-desc">{{ corner.description }}</p>
                <div class="corner-stats">
                  <span class="stat">
                    <span class="stat-icon">📝</span>
                    {{ corner.post_count || 0 }} posts
                  </span>
                  <span class="stat">
                    <span class="stat-icon">❤️</span>
                    {{ corner.total_likes || 0 }}
                  </span>
                  <span v-if="corner.distance" class="stat distance">
                    <span class="stat-icon">📍</span>
                    {{ formatDistance(corner.distance) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tag Filter (for recommendation) -->
      <div v-if="currentFeedType === 'recommendation'" class="tag-filter-section">
        <div class="tag-input-container">
          <div class="tag-input-wrapper">
            <span class="tag-icon">#</span>
            <input
              v-model="tagInput"
              type="text"
              placeholder="Enter tag to filter posts..."
              @keyup.enter="addTag"
            />
            <button v-if="tagInput" @click="clearTagInput" class="clear-tag">×</button>
          </div>
          <button @click="addTag" class="filter-button">Filter</button>
        </div>

        <!-- Selected Tags -->
        <div v-if="selectedTags.length > 0" class="selected-tags">
          <span
            v-for="(tag, index) in selectedTags"
            :key="index"
            class="selected-tag"
          >
            #{{ tag }}
            <button @click="removeTag(index)" class="remove-tag">×</button>
          </span>
          <button @click="clearAllTags" class="clear-all-tags">Clear all</button>
        </div>
      </div>

      <div v-if="error && currentFeedType !== 'finding'" class="error-message">{{ error }}</div>

      <div v-else-if="displayPosts.length === 0 && !isLoading && currentFeedType !== 'finding'" class="empty-state">
        <p v-if="selectedTags.length > 0">
          No posts found with tags: {{ selectedTags.map(t => '#' + t).join(', ') }}
        </p>
        <p v-else-if="currentFeedType === 'following'">
          You're not following anyone yet. Discover interesting content!
        </p>
        <p v-else>
          No recommendations yet. Explore and interact with content to get personalized recommendations!
        </p>
      </div>

      <div v-if="currentFeedType !== 'finding'" class="posts-list">
        <PostCard
          v-for="post in displayPosts"
          :key="post._id"
          :post="post"
          compact
          @view="trackView(post._id)"
          @deleted="handlePostDeleted"
        />
      </div>

      <div v-if="isLoading && selectedTags.length === 0 && currentFeedType !== 'finding'" class="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>

      <div v-if="selectedTags.length === 0 && !hasMore && displayPosts.length > 0 && currentFeedType !== 'finding'" class="end-message">
        <p>You've reached the end</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { feedApi } from '../api/feed';
import { recommendationsApi } from '../api/recommendations';
import { postsApi } from '../api/posts';
import { cornersApi } from '../api/corners';
import { mediaApi } from '../api/media';
import PostCard from '../components/Feed/PostCard.vue';

const router = useRouter();

// Define reactive state directly, without nested composables
const posts = ref([]);
const loading = ref(false);
const error = ref(null);
const hasMore = ref(true);
const skip = ref(0);
const limit = 20;

const currentFeedType = ref('following');
const tagInput = ref('');
const selectedTags = ref([]);
const filteredPosts = ref([]);
const tagFilterLoading = ref(false);
const userLocation = ref(null);

const viewTimers = ref(new Map());

// Finding state
const hotCorners = ref([]);
const hotLoading = ref(false);
const searchQuery = ref('');
const searchResults = ref([]);
const searchLoading = ref(false);
const showSearchResults = ref(false);

// Simple computed
const isLoading = computed(() => loading.value || tagFilterLoading.value);

const displayPosts = computed(() => {
  return selectedTags.value.length > 0 ? filteredPosts.value : posts.value;
});

// Get user location
const getUserLocation = () => {
  return new Promise((resolve) => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        () => {
          resolve({ lat: 31.2304, lng: 121.4737 }); // Default: Shanghai
        }
      );
    } else {
      resolve({ lat: 31.2304, lng: 121.4737 });
    }
  });
};

// Fetch data directly
const fetchPosts = async (reset = false) => {
  if (reset) {
    skip.value = 0;
    posts.value = [];
  }

  loading.value = true;
  error.value = null;

  try {
    let response;

    if (currentFeedType.value === 'following') {
      response = await feedApi.getFollowing({
        skip: skip.value,
        limit,
        include_own: true
      });
    } else {
      // recommendation
      if (!userLocation.value) {
        userLocation.value = await getUserLocation();
      }
      response = await recommendationsApi.getFeed({
        lat: userLocation.value.lat,
        lng: userLocation.value.lng,
        skip: skip.value,
        limit
      });
    }

    console.log('[FeedView] API response:', response);

    if (response.success && response.data?.posts) {
      const newPosts = response.data.posts;
      if (reset) {
        posts.value = newPosts;
      } else {
        posts.value = [...posts.value, ...newPosts];
      }
      skip.value += newPosts.length;
      hasMore.value = newPosts.length === limit;
      console.log('[FeedView] posts updated:', posts.value.length, posts.value);
    }
  } catch (err) {
    error.value = err.error?.message || 'Loading failed';
    console.error('[FeedView] fetch error:', err);
  } finally {
    loading.value = false;
  }
};

// Fetch hot corners
const fetchHotCorners = async () => {
  hotLoading.value = true;
  
  try {
    if (!userLocation.value) {
      userLocation.value = await getUserLocation();
    }
    
    const response = await cornersApi.getHot({
      lat: userLocation.value.lat,
      lng: userLocation.value.lng,
      limit: 20
    });
    
    if (response.success && response.data?.corners) {
      hotCorners.value = response.data.corners;
    }
  } catch (err) {
    console.error('Failed to fetch hot corners:', err);
  } finally {
    hotLoading.value = false;
  }
};

// Search corners
const searchCorners = async () => {
  const query = searchQuery.value.trim();
  if (!query) return;
  
  searchLoading.value = true;
  showSearchResults.value = true;
  
  try {
    const response = await cornersApi.search(query, { limit: 20 });
    
    if (response.success && response.data?.corners) {
      searchResults.value = response.data.corners;
    }
  } catch (err) {
    console.error('Failed to search corners:', err);
    searchResults.value = [];
  } finally {
    searchLoading.value = false;
  }
};

const clearSearch = () => {
  searchQuery.value = '';
  searchResults.value = [];
  showSearchResults.value = false;
};

// Navigate to corner
const goToCorner = (corner) => {
  router.push({
    path: '/map',
    query: {
      corner_id: corner._id,
      lat: corner.location?.coordinates?.[1],
      lng: corner.location?.coordinates?.[0]
    }
  });
};

// Helper functions
const getMediaUrl = (fileId) => {
  return mediaApi.getUrl(fileId);
};

const formatDistance = (meters) => {
  if (!meters) return '';
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
};

const getRankClass = (index) => {
  if (index === 0) return 'gold';
  if (index === 1) return 'silver';
  if (index === 2) return 'bronze';
  return '';
};

const loadMore = () => {
  if (!loading.value && hasMore.value) {
    fetchPosts(false);
  }
};

const refresh = () => {
  if (currentFeedType.value === 'finding') {
    fetchHotCorners();
  } else {
    fetchPosts(true);
  }
};

const switchFeed = (type) => {
  if (currentFeedType.value === type) return;

  currentFeedType.value = type;
  tagInput.value = '';
  selectedTags.value = [];
  filteredPosts.value = [];
  searchQuery.value = '';
  searchResults.value = [];
  showSearchResults.value = false;
  
  // Clear view timers
  viewTimers.value.forEach(timer => clearTimeout(timer));
  viewTimers.value.clear();
  
  if (type === 'finding') {
    fetchHotCorners();
  } else {
    refresh();
  }
};

const handlePostDeleted = (postId) => {
  // Remove from posts
  const index = posts.value.findIndex(p => p._id === postId);
  if (index > -1) {
    posts.value.splice(index, 1);
  }
  
  // Remove from filtered posts
  const filteredIndex = filteredPosts.value.findIndex(p => p._id === postId);
  if (filteredIndex > -1) {
    filteredPosts.value.splice(filteredIndex, 1);
  }
};

const addTag = async () => {
  const tag = tagInput.value.trim();
  if (!tag) return;

  // Check if tag already exists
  if (selectedTags.value.includes(tag)) {
    tagInput.value = '';
    return;
  }

  // Add tag to selected tags
  selectedTags.value.push(tag);
  tagInput.value = '';

  // Search with all selected tags (AND logic)
  await searchWithTags();
};

const removeTag = async (index) => {
  selectedTags.value.splice(index, 1);
  await searchWithTags();
};

const clearAllTags = async () => {
  selectedTags.value = [];
  filteredPosts.value = [];
};

const clearTagInput = () => {
  tagInput.value = '';
};

const searchWithTags = async () => {
  if (selectedTags.value.length === 0) {
    filteredPosts.value = [];
    return;
  }

  tagFilterLoading.value = true;
  try {
    // Use POST API with JSON body for tag search
    const response = await postsApi.searchByTags({ tags: selectedTags.value, limit: 50 });
    if (response.success && response.data) {
      filteredPosts.value = response.data.posts || [];
    }
  } catch (err) {
    console.error('Failed to filter by tags:', err);
    filteredPosts.value = [];
  } finally {
    tagFilterLoading.value = false;
  }
};

const trackView = (postId) => {
  if (viewTimers.value.has(postId)) return;

  const timer = setTimeout(async () => {
    try {
      const { viewHistoryApi } = await import('../api/view_history');
      await viewHistoryApi.recordView(postId, 10000);
    } catch (err) {
      console.error('Failed to track view:', err);
    } finally {
      viewTimers.value.delete(postId);
    }
  }, 10000);

  viewTimers.value.set(postId, timer);
};

// Infinite scroll
let observer = null;
let loadMoreTrigger = null;

const setupInfiniteScroll = () => {
  const options = {
    root: null,
    rootMargin: '100px',
    threshold: 0
  };

  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && hasMore.value && !loading.value) {
      loadMore();
    }
  }, options);

  loadMoreTrigger = document.createElement('div');
  loadMoreTrigger.className = 'load-more-trigger';
  const feedView = document.querySelector('.feed-view');
  if (feedView) {
    feedView.appendChild(loadMoreTrigger);
    observer.observe(loadMoreTrigger);
  }
};

onMounted(() => {
  refresh();
  setupInfiniteScroll();
});

onUnmounted(() => {
  if (observer) {
    observer.disconnect();
  }
  if (loadMoreTrigger && loadMoreTrigger.parentNode) {
    loadMoreTrigger.parentNode.removeChild(loadMoreTrigger);
  }
  viewTimers.value.forEach(timer => clearTimeout(timer));
  viewTimers.value.clear();
});
</script>

<style scoped>
.feed-view {
  height: 100%;
  width: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.feed-container {
  max-width: 600px;
  margin: 0 auto;
}

.feed-toggle {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 6px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toggle-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 15px;
  font-weight: 500;
  color: #666;
}

.toggle-button:hover {
  background: #f5f5f5;
}

.toggle-button.active {
  background: linear-gradient(135deg, #667eea 0%, #4a6478 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.toggle-icon {
  font-size: 18px;
}

.tag-filter-section {
  margin-bottom: 20px;
}

.tag-input-container {
  display: flex;
  gap: 8px;
  align-items: stretch;
  margin-bottom: 12px;
}

.tag-filter {
  margin-bottom: 20px;
  display: flex;
  gap: 8px;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0 0 0;
  align-items: center;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #667eea 0%, #4a6478 100%);
  color: white;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.remove-tag {
  background: none;
  border: none;
  color: white;
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.remove-tag:hover {
  background: rgba(255, 255, 255, 0.2);
}

.clear-all-tags {
  padding: 6px 12px;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-all-tags:hover {
  background: #e0e0e0;
  color: #333;
}

.tag-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  transition: border-color 0.3s;
}

.tag-input-wrapper:focus-within {
  border-color: #409eff;
}

.tag-icon {
  font-size: 18px;
  color: #667eea;
}

.tag-input-wrapper input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
}

.clear-tag {
  background: none;
  border: none;
  color: #999;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-tag:hover {
  color: #333;
}

.filter-button {
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #3b82f6 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.filter-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.error-message {
  padding: 20px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 8px;
  text-align: center;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: #999;
}

.posts-list {
  margin-bottom: 20px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.end-message {
  padding: 20px;
  text-align: center;
  color: #999;
}

.load-more-trigger {
  height: 1px;
}

/* Finding Section Styles */
.finding-section {
  margin-bottom: 20px;
}

.search-section {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  transition: border-color 0.3s;
}

.search-input-wrapper:focus-within {
  border-color: #409eff;
}

.search-icon {
  font-size: 18px;
}

.search-input-wrapper input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
}

.clear-search {
  background: none;
  border: none;
  color: #999;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.section-header .subtitle {
  font-size: 14px;
  color: #999;
}

.back-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #409eff;
  font-size: 14px;
  cursor: pointer;
}

.back-btn:hover {
  color: #66b1ff;
}

.corners-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.corner-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.corner-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.rank-badge {
  position: absolute;
  top: -8px;
  left: -8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  color: white;
  background: #999;
  z-index: 1;
}

.rank-badge.gold {
  background: linear-gradient(135deg, #ffd700, #ffb800);
}

.rank-badge.silver {
  background: linear-gradient(135deg, #c0c0c0, #a8a8a8);
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #cd7f32, #b8722e);
}

.corner-image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f5f5f5;
}

.corner-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.corner-content {
  flex: 1;
  min-width: 0;
}

.corner-name {
  margin: 0 0 6px 0;
  font-size: 16px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.corner-desc {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #666;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.corner-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

.corner-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.corner-stats .stat {
  display: flex;
  align-items: center;
  gap: 4px;
}

.corner-stats .stat-icon {
  font-size: 14px;
}

.distance {
  color: #409eff;
}

.tags {
  color: #667eea;
}

/* Mobile Responsive */
@media (max-width: 600px) {
  .feed-toggle {
    flex-wrap: wrap;
  }
  
  .toggle-button {
    min-width: calc(33% - 4px);
    padding: 10px 8px;
    font-size: 13px;
  }
  
  .search-section {
    flex-direction: column;
  }
  
  .search-btn {
    width: 100%;
  }
  
  .corner-card {
    padding: 12px;
  }
  
  .corner-image {
    width: 60px;
    height: 60px;
  }
  
  .corner-name {
    font-size: 14px;
  }
  
  .corner-stats {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>

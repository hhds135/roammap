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
          :class="['toggle-button', { active: currentFeedType === 'recommendation' }]"
          @click="switchFeed('recommendation')"
        >
          <span class="toggle-icon">✨</span>
          <span>Recommended</span>
        </button>
      </div>

      <!-- Tag Filter -->
      <div v-if="currentFeedType === 'recommendation'" class="tag-filter">
        <div class="tag-input-wrapper">
          <span class="tag-icon">#</span>
          <input
            v-model="tagFilter"
            type="text"
            placeholder="Enter tag to filter posts..."
            @keyup.enter="applyTagFilter"
          />
          <button v-if="tagFilter" @click="clearTagFilter" class="clear-tag">×</button>
        </div>
        <button @click="applyTagFilter" class="filter-button">Filter</button>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div v-else-if="displayPosts.length === 0 && !isLoading" class="empty-state">
        <p v-if="tagFilter">
          No posts found with "#{{ tagFilter }}" tag
        </p>
        <p v-else-if="currentFeedType === 'following'">
          You're not following anyone yet. Discover interesting content!
        </p>
        <p v-else>
          No recommendations yet. Explore and interact with content to get personalized recommendations!
        </p>
      </div>

      <div v-else class="posts-list">
        <PostCard
          v-for="post in displayPosts"
          :key="post._id"
          :post="post"
          compact
          @view="trackView(post._id)"
          @deleted="handlePostDeleted"
        />
      </div>

      <div v-if="isLoading && !tagFilter" class="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>

      <div v-if="!tagFilter && !hasMore && displayPosts.length > 0" class="end-message">
        <p>You've reached the end</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { feedApi } from '../api/feed';
import { recommendationsApi } from '../api/recommendations';
import { postsApi } from '../api/posts';
import PostCard from '../components/Feed/PostCard.vue';

// 直接定义响应式状态，不使用嵌套的 composable
const posts = ref([]);
const loading = ref(false);
const error = ref(null);
const hasMore = ref(true);
const skip = ref(0);
const limit = 20;

const currentFeedType = ref('following');
const tagFilter = ref('');
const filteredPosts = ref([]);
const tagFilterLoading = ref(false);
const userLocation = ref(null);

const viewTimers = ref(new Map());

// 简单的 computed
const isLoading = computed(() => loading.value || tagFilterLoading.value);

const displayPosts = computed(() => {
  return tagFilter.value ? filteredPosts.value : posts.value;
});

// 获取用户位置
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

// 直接获取数据
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

const loadMore = () => {
  if (!loading.value && hasMore.value) {
    fetchPosts(false);
  }
};

const refresh = () => {
  fetchPosts(true);
};

const switchFeed = (type) => {
  if (currentFeedType.value === type) return;
  
  currentFeedType.value = type;
  tagFilter.value = '';
  filteredPosts.value = [];
  
  // Clear view timers
  viewTimers.value.forEach(timer => clearTimeout(timer));
  viewTimers.value.clear();
  
  refresh();
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

const applyTagFilter = async () => {
  const tag = tagFilter.value.trim();
  if (!tag) return;

  tagFilterLoading.value = true;
  try {
    const response = await postsApi.getAll({ tag, limit: 50 });
    if (response.success && response.data) {
      filteredPosts.value = response.data.posts || [];
    }
  } catch (err) {
    console.error('Failed to filter by tag:', err);
    filteredPosts.value = [];
  } finally {
    tagFilterLoading.value = false;
  }
};

const clearTagFilter = () => {
  tagFilter.value = '';
  filteredPosts.value = [];
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
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.toggle-icon {
  font-size: 18px;
}

.tag-filter {
  margin-bottom: 20px;
  display: flex;
  gap: 8px;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
</style>

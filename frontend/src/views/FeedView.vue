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

      <div v-if="error" class="error-message">{{ error }}</div>

      <div v-else-if="posts.length === 0 && !loading" class="empty-state">
        <p v-if="currentFeedType === 'following'">
          You're not following anyone yet. Discover interesting content!
        </p>
        <p v-else>
          No recommendations yet. Explore and interact with content to get personalized recommendations!
        </p>
      </div>

      <div v-else class="posts-list">
        <PostCard
          v-for="post in posts"
          :key="post._id"
          :post="post"
          @view="trackView(post._id)"
        />
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>

      <div v-if="!hasMore && posts.length > 0" class="end-message">
        <p>You've reached the end</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useFeed } from '../composables/useFeed';
import PostCard from '../components/Feed/PostCard.vue';

const currentFeedType = ref('following');
const viewTimers = ref(new Map());

// Initialize feed
const {
  posts,
  loading,
  error,
  hasMore,
  loadMore,
  refresh,
  userLocation
} = useFeed(currentFeedType.value);

const switchFeed = (type) => {
  if (currentFeedType.value === type) return;

  currentFeedType.value = type;

  // Clear view timers
  viewTimers.value.forEach(timer => clearTimeout(timer));
  viewTimers.value.clear();

  // Reinitialize feed with new type
  Object.assign(useFeed(type));
  refresh();
};

// Track post view after 10 seconds
const trackView = (postId) => {
  if (viewTimers.value.has(postId)) return;

  const timer = setTimeout(async () => {
    try {
      // Record view with 10 seconds duration (10000 ms)
      const { viewHistoryApi } = await import('../api/view_history');
      await viewHistoryApi.recordView(postId, 10000);
      console.log(`View tracked for post: ${postId}`);
    } catch (err) {
      console.error('Failed to track view:', err);
    } finally {
      viewTimers.value.delete(postId);
    }
  }, 10000); // 10 seconds

  viewTimers.value.set(postId, timer);
};

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
  document.querySelector('.feed-view').appendChild(loadMoreTrigger);
  observer.observe(loadMoreTrigger);
};

onMounted(() => {
  setupInfiniteScroll();
});

onUnmounted(() => {
  if (observer) {
    observer.disconnect();
  }
  if (loadMoreTrigger) {
    loadMoreTrigger.remove();
  }
  // Clear all view timers
  viewTimers.value.forEach(timer => clearTimeout(timer));
  viewTimers.value.clear();
});
</script>

<style scoped>
.feed-view {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
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
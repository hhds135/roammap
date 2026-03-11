<template>
  <div class="feed-view">
    <div class="feed-container">
      <h1 class="feed-title">Following Feed</h1>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div v-else-if="posts.length === 0 && !loading" class="empty-state">
        <p>You're not following anyone yet. Discover interesting content!</p>
      </div>

      <div v-else class="posts-list">
        <PostCard
          v-for="post in posts"
          :key="post._id"
          :post="post"
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
import { onMounted, onUnmounted } from 'vue';
import { useFeed } from '../composables/useFeed';
import PostCard from '../components/Feed/PostCard.vue';

const { posts, loading, error, hasMore, loadMore } = useFeed('following');

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

.feed-title {
  margin-bottom: 20px;
  color: #333;
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
<template>
  <div class="favorites-view">
    <div class="favorites-container">
      <div class="favorites-header">
        <h1>My Favorites</h1>
        <p v-if="total > 0" class="subtitle">{{ total }} favorites total</p>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>

      <div v-else-if="favorites.length === 0" class="empty-state">
        <div class="empty-icon">⭐</div>
        <p>No posts favorited yet</p>
        <p class="empty-hint">Go to Feed page to discover interesting content!</p>
      </div>

      <div v-else class="favorites-list">
        <PostCard
          v-for="item in favorites"
          :key="item.post._id"
          :post="item.post"
        />
      </div>

      <div v-if="hasMore && !loading" class="load-more">
        <button @click="loadMore" class="load-more-btn">
          Load More
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useAuth } from '../composables/useAuth';
import { favoritesApi } from '../api/favorites';
import PostCard from '../components/Feed/PostCard.vue';

const { user: currentUser } = useAuth();

const favorites = ref([]);
const loading = ref(false);
const total = ref(0);
const skip = ref(0);
const limit = 20;
const hasMore = ref(false);

const loadFavorites = async () => {
  if (!currentUser.value) {
    return;
  }

  loading.value = true;
  try {
    const response = await favoritesApi.getUserFavorites(currentUser.value.id, {
      skip: skip.value,
      limit
    });

    if (response.success && response.data) {
      if (skip.value === 0) {
        favorites.value = response.data.favorites || [];
      } else {
        favorites.value = [...favorites.value, ...(response.data.favorites || [])];
      }
      total.value = response.data.total || 0;
      hasMore.value = favorites.value.length < total.value;
    }
  } catch (error) {
    console.error('Failed to load favorites:', error);
  } finally {
    loading.value = false;
  }
};

const loadMore = () => {
  skip.value += limit;
  loadFavorites();
};

onMounted(() => {
  loadFavorites();
});
</script>

<style scoped>
.favorites-view {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  background: #f5f5f5;
}

.favorites-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.favorites-header {
  margin-bottom: 24px;
}

.favorites-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 4px 0;
  color: #666;
}

.empty-hint {
  font-size: 14px;
  color: #999;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.load-more-btn {
  padding: 12px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.load-more-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.load-more-btn:active {
  transform: translateY(0);
}
</style>
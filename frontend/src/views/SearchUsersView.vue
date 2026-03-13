<template>
  <div class="search-users-view">
    <div class="search-container">
      <!-- Search Input -->
      <div class="search-header">
        <h1>Search Users</h1>
        <div class="search-input-wrapper">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Enter username to search..."
            @keyup.enter="handleSearch"
          />
          <button v-if="searchQuery" @click="clearSearch" class="clear-button">×</button>
        </div>
        <button @click="handleSearch" class="search-button">Search</button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Searching...</p>
      </div>

      <!-- Results -->
      <div v-else-if="hasSearched && users.length === 0" class="empty-state">
        <div class="empty-icon">👤</div>
        <p>No matching users found</p>
        <p class="empty-hint">Try using different keywords</p>
      </div>

      <!-- User List -->
      <div v-else-if="users.length > 0" class="results-section">
        <div class="results-header">
          <h2>Search Results</h2>
          <span class="results-count">{{ total }} users</span>
        </div>
        
        <div class="user-list">
          <div v-for="user in users" :key="user._id" class="user-card">
            <div class="user-avatar">{{ user.username.charAt(0).toUpperCase() }}</div>
            <div class="user-info">
              <h3 class="user-name">{{ user.username }}</h3>
              <div class="user-stats">
                <span>👥 {{ user.followers_count }} followers</span>
                <span>👣 {{ user.following_count }} following</span>
              </div>
              <div v-if="user.interest_tags && user.interest_tags.length > 0" class="user-tags">
                <span v-for="tag in user.interest_tags.slice(0, 3)" :key="tag" class="tag">
                  #{{ tag }}
                </span>
                <span v-if="user.interest_tags.length > 3" class="more-tags">
                  +{{ user.interest_tags.length - 3 }}
                </span>
              </div>
            </div>
            <div class="user-actions">
              <button @click="viewProfile(user._id)" class="btn-view">View Profile</button>
              <FollowButton :target-user-id="user._id" />
            </div>
          </div>
        </div>
      </div>

      <!-- Initial State -->
      <div v-else class="empty-state">
        <div class="empty-icon">🔍</div>
        <p>Enter username to start searching</p>
        <p class="empty-hint">You can search other users' usernames to find them</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { usersApi } from '../api/users';
import FollowButton from '../components/User/FollowButton.vue';

const router = useRouter();

const searchQuery = ref('');
const users = ref([]);
const loading = ref(false);
const hasSearched = ref(false);
const total = ref(0);

const handleSearch = async () => {
  const query = searchQuery.value.trim();
  if (!query) {
    return;
  }

  loading.value = true;
  hasSearched.value = true;

  try {
    const response = await usersApi.search(query, { limit: 20 });
    if (response.success && response.data) {
      users.value = response.data.users || [];
      total.value = response.data.total || 0;
    }
  } catch (error) {
    console.error('Search failed:', error);
    users.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

const clearSearch = () => {
  searchQuery.value = '';
  users.value = [];
  hasSearched.value = false;
  total.value = 0;
};

const viewProfile = (userId) => {
  router.push(`/profile/${userId}`);
};
</script>

<style scoped>
.search-users-view {
  height: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.search-container {
  max-width: 800px;
  margin: 0 auto;
}

.search-header {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.search-header h1 {
  margin: 0 0 16px 0;
  font-size: 24px;
  color: #333;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 12px;
  border: 2px solid transparent;
  transition: border-color 0.3s;
}

.search-input-wrapper:focus-within {
  border-color: #409eff;
  background: white;
}

.search-icon {
  font-size: 20px;
}

.search-input-wrapper input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 15px;
}

.clear-button {
  background: none;
  border: none;
  color: #999;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-button:hover {
  color: #333;
}

.search-button {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.search-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  color: #666;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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

.results-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.results-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.results-count {
  font-size: 14px;
  color: #999;
}

.user-list {
  display: flex;
  flex-direction: column;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.user-card:last-child {
  border-bottom: none;
}

.user-card:hover {
  background: #fafafa;
}

.user-avatar {
  width: 56px;
  height: 56px;
  min-width: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 22px;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.user-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 10px;
  background: #f0f4ff;
  color: #667eea;
  border-radius: 12px;
  font-size: 12px;
}

.more-tags {
  font-size: 12px;
  color: #999;
}

.user-actions {
  display: flex;
  gap: 8px;
}

.btn-view {
  padding: 8px 16px;
  background: white;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-view:hover {
  border-color: #409eff;
  color: #409eff;
}
</style>
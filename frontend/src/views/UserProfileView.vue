<template>
  <div class="user-profile-view">
    <div class="profile-container">
      <!-- User Info Header -->
      <div class="profile-header">
        <div class="avatar" :style="avatarStyle">
          <img v-if="user?.avatar_id" :src="avatarUrl" alt="Avatar" @error="handleAvatarError" />
          <span v-else class="avatar-initial">{{ displayInitial }}</span>
        </div>
        <div class="user-info">
          <div class="user-name-row">
            <h1>{{ displayName }}</h1>
            <div v-if="isSelf" class="action-buttons">
              <button @click="goToEditProfile" class="edit-btn">
                Edit Profile
              </button>
              <button @click="handleLogout" class="logout-btn">
                Logout
              </button>
            </div>
          </div>
          <div class="username-hint" v-if="user?.nickname && user.nickname !== user.username">
            @{{ user.username }}
          </div>
          <div class="stats">
            <div class="stat-item clickable" @click="switchTab('posts')">
              <span class="stat-number">{{ postsCount }}</span>
              <span class="stat-label">Posts</span>
            </div>
            <div v-if="isSelf" class="stat-item clickable" @click="switchTab('corners')">
              <span class="stat-number">{{ cornersCount }}</span>
              <span class="stat-label">Corners</span>
            </div>
            <div class="stat-item clickable" @click="switchTab('following')">
              <span class="stat-number">{{ followingCount }}</span>
              <span class="stat-label">Following</span>
            </div>
            <div class="stat-item clickable" @click="switchTab('followers')">
              <span class="stat-number">{{ followersCount }}</span>
              <span class="stat-label">Followers</span>
            </div>
            <div v-if="isSelf" class="stat-item clickable" @click="switchTab('favorites')">
              <span class="stat-number">{{ favoritesCount }}</span>
              <span class="stat-label">Favorites</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Follow Button (for other users) -->
      <div v-if="!isSelf && user" class="follow-section">
        <FollowButton :target-user-id="user.id" />
      </div>

      <!-- Interest Tags -->
      <div v-if="user && user.interest_tags && user.interest_tags.length > 0" class="interests-section">
        <h3>Interests</h3>
        <div class="tags-list">
          <span v-for="(tag, idx) in user.interest_tags" :key="idx" class="tag-chip">
            #{{ tag }}
          </span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs-section">
        <div class="tabs">
          <button
            :class="['tab-btn', { active: activeTab === 'posts' }]"
            @click="switchTab('posts')"
          >
            Posts
          </button>
          <button
            v-if="isSelf"
            :class="['tab-btn', { active: activeTab === 'corners' }]"
            @click="switchTab('corners')"
          >
            Corners
          </button>
          <button
            :class="['tab-btn', { active: activeTab === 'following' }]"
            @click="switchTab('following')"
          >
            Following
          </button>
          <button
            :class="['tab-btn', { active: activeTab === 'followers' }]"
            @click="switchTab('followers')"
          >
            Followers
          </button>
          <button
            v-if="isSelf"
            :class="['tab-btn', { active: activeTab === 'favorites' }]"
            @click="switchTab('favorites')"
          >
            Favorites
          </button>
        </div>
      </div>

      <!-- User's Posts -->
      <div v-if="user && activeTab === 'posts'" class="posts-section">
        <h3>{{ isSelf ? 'My Posts' : 'Posts' }}</h3>
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>
        <div v-else-if="posts.length === 0" class="empty-state">
          <p>No posts yet</p>
        </div>
        <div v-else class="posts-list">
          <PostCard
            v-for="post in posts"
            :key="post._id"
            :post="post"
            compact
            @deleted="handlePostDeleted"
          />
        </div>
      </div>

      <!-- User's Corners (only for self) -->
      <div v-if="user && isSelf && activeTab === 'corners'" class="corners-section">
        <h3>My Corners</h3>
        <div v-if="loadingCorners" class="loading">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>
        <div v-else-if="corners.length === 0" class="empty-state">
          <p>No corners created yet</p>
        </div>
        <div v-else class="corners-list">
          <div
            v-for="corner in corners"
            :key="corner._id"
            class="corner-item"
            @click="goToMap(corner)"
          >
            <div class="corner-images">
              <img
                v-if="corner.images && corner.images.length > 0"
                :src="getMediaUrl(corner.images[0])"
                :alt="corner.name"
              />
              <div v-else class="corner-placeholder">
                <span class="placeholder-icon">📍</span>
              </div>
            </div>
            <div class="corner-info">
              <h4 class="corner-name">{{ corner.name }}</h4>
              <p v-if="corner.description" class="corner-description">{{ corner.description }}</p>
              <div class="corner-meta">
                <span class="corner-posts">{{ corner.postCount || 0 }} posts</span>
                <button 
                  @click.stop="editCorner(corner)" 
                  class="edit-corner-btn"
                >
                  Edit
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Following List -->
      <div v-if="user && activeTab === 'following'" class="users-section">
        <h3>Following</h3>
        <div v-if="loadingFollowing" class="loading">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>
        <div v-else-if="followingList.length === 0" class="empty-state">
          <p>Not following anyone yet</p>
        </div>
        <div v-else class="users-list">
          <div
            v-for="followedUser in followingList"
            :key="followedUser.user_id"
            class="user-item"
            @click="goToProfile(followedUser.user_id)"
          >
            <div class="user-avatar">{{ followedUser.username.charAt(0).toUpperCase() }}</div>
            <div class="user-details">
              <span class="user-name">{{ followedUser.username }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Followers List -->
      <div v-if="user && activeTab === 'followers'" class="users-section">
        <h3>Followers</h3>
        <div v-if="loadingFollowers" class="loading">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>
        <div v-else-if="followersList.length === 0" class="empty-state">
          <p>No followers yet</p>
        </div>
        <div v-else class="users-list">
          <div
            v-for="follower in followersList"
            :key="follower.user_id"
            class="user-item"
            @click="goToProfile(follower.user_id)"
          >
            <div class="user-avatar">{{ follower.username.charAt(0).toUpperCase() }}</div>
            <div class="user-details">
              <span class="user-name">{{ follower.username }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Favorites List -->
      <div v-if="user && isSelf && activeTab === 'favorites'" class="favorites-section">
        <h3>My Favorites</h3>
        <div v-if="loadingFavorites" class="loading">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>
        <div v-else-if="favorites.length === 0" class="empty-state">
          <p>No favorites yet</p>
        </div>
        <div v-else class="posts-list">
          <PostCard
            v-for="post in favorites"
            :key="post._id"
            :post="post"
            compact
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onActivated } from 'vue';
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { followsApi } from '../api/follows';
import { postsApi } from '../api/posts';
import { cornersApi } from '../api/corners';
import { usersApi } from '../api/users';
import { favoritesApi } from '../api/favorites';
import { mediaApi } from '../api/media';
import PostCard from '../components/Feed/PostCard.vue';
import FollowButton from '../components/User/FollowButton.vue';

const router = useRouter();
const route = useRoute();
const { user: currentUser, logout } = useAuth();

const user = ref(null);
const posts = ref([]);
const corners = ref([]);
const followingList = ref([]);
const followersList = ref([]);
const favorites = ref([]);
const followingCount = ref(0);
const followersCount = ref(0);
const postsCount = ref(0);
const cornersCount = ref(0);
const favoritesCount = ref(0);
const loading = ref(false);
const loadingCorners = ref(false);
const loadingFollowing = ref(false);
const loadingFollowers = ref(false);
const loadingFavorites = ref(false);
const activeTab = ref('posts');

const isSelf = computed(() => {
  return !route.params.userId || currentUser.value?.id === route.params.userId;
});

const displayName = computed(() => {
  // Show nickname if available, otherwise show username (for backwards compatibility)
  return user.value?.nickname || user.value?.username || 'Unknown User';
});

const displayInitial = computed(() => {
  const name = displayName.value;
  return name?.charAt(0)?.toUpperCase() || 'U';
});

const avatarError = ref(false);

const avatarUrl = computed(() => {
  if (user.value?.avatar_id) {
    return mediaApi.getUrl(user.value.avatar_id);
  }
  return '';
});

const avatarStyle = computed(() => {
  if (user.value?.avatar_id && !avatarError.value) {
    return {};
  }
  return {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  };
});

const handleAvatarError = () => {
  avatarError.value = true;
};

const goToEditProfile = () => {
  router.push('/edit-profile');
};

const switchTab = (tab) => {
  activeTab.value = tab;
  const userId = user.value?.id || currentUser.value?.id;
  
  if (!userId) return;

  if (tab === 'corners' && corners.value.length === 0) {
    loadUserCorners(userId);
  } else if (tab === 'following' && followingList.value.length === 0) {
    loadFollowing(userId);
  } else if (tab === 'followers' && followersList.value.length === 0) {
    loadFollowers(userId);
  } else if (tab === 'favorites' && favorites.value.length === 0 && isSelf.value) {
    loadFavorites();
  }
};

const loadUserProfile = async () => {
  const userId = route.params.userId || currentUser.value?.id;

  if (!userId) {
    return;
  }

  try {
    // Always fetch fresh user data from API (including interest_tags, nickname, avatar_id)
    const interestsResponse = await usersApi.getInterests(userId);
    if (interestsResponse.success && interestsResponse.data) {
      user.value = {
        id: userId,
        username: interestsResponse.data.username,
        nickname: interestsResponse.data.nickname || '',
        avatar_id: interestsResponse.data.avatar_id || '',
        interest_tags: interestsResponse.data.interest_tags
      };
    }

    await loadUserStats(userId);
    await loadUserPosts(userId);
  } catch (err) {
    console.error('Failed to load user profile:', err);
  }
};

const loadUserStats = async (userId) => {
  try {
    const [following, followers, postsResponse, cornersResponse] = await Promise.all([
      followsApi.getFollowing(userId, { limit: 1 }),
      followsApi.getFollowers(userId, { limit: 1 }),
      postsApi.list({ user_id: userId, limit: 1 }),
      cornersApi.getAll({ user_id: userId, limit: 1 })
    ]);

    if (following.success) {
      followingCount.value = following.data?.total || 0;
    }
    if (followers.success) {
      followersCount.value = followers.data?.total || 0;
    }
    if (postsResponse.success) {
      postsCount.value = postsResponse.data?.total || 0;
    }
    if (cornersResponse.success && cornersResponse.data?.corners) {
      cornersCount.value = cornersResponse.data.total || 0;
    }
    
    // Load favorites count only for own profile
    if (isSelf.value) {
      const favoritesResponse = await favoritesApi.getUserFavorites(userId, { limit: 1 });
      if (favoritesResponse.success && favoritesResponse.data?.favorites) {
        favoritesCount.value = favoritesResponse.data.favorites.length;
      }
    }
  } catch (err) {
    console.error('Failed to load user stats:', err);
  }
};

const loadUserPosts = async (userId) => {
  loading.value = true;
  try {
    const response = await postsApi.list({
      user_id: userId,
      limit: 20,
      skip: 0
    });

    if (response.success && response.data?.posts) {
      posts.value = response.data.posts;
    }
  } catch (err) {
    console.error('Failed to load user posts:', err);
  } finally {
    loading.value = false;
  }
};

const loadUserCorners = async (userId) => {
  loadingCorners.value = true;
  try {
    // Get corners created by this user only
    const response = await cornersApi.getAll({ 
      user_id: userId,
      limit: 100 
    });
    
    if (response.success && response.data?.corners) {
      corners.value = response.data.corners;
    }
  } catch (err) {
    console.error('Failed to load user corners:', err);
  } finally {
    loadingCorners.value = false;
  }
};

const loadFollowing = async (userId) => {
  loadingFollowing.value = true;
  try {
    const response = await followsApi.getFollowing(userId, { limit: 100 });
    if (response.success && response.data?.following) {
      followingList.value = response.data.following;
    }
  } catch (err) {
    console.error('Failed to load following:', err);
  } finally {
    loadingFollowing.value = false;
  }
};

const loadFollowers = async (userId) => {
  loadingFollowers.value = true;
  try {
    const response = await followsApi.getFollowers(userId, { limit: 100 });
    if (response.success && response.data?.followers) {
      followersList.value = response.data.followers;
    }
  } catch (err) {
    console.error('Failed to load followers:', err);
  } finally {
    loadingFollowers.value = false;
  }
};

const loadFavorites = async () => {
  if (!currentUser.value) return;
  
  loadingFavorites.value = true;
  try {
    const response = await favoritesApi.getUserFavorites(currentUser.value.id, { limit: 50 });
    if (response.success && response.data?.favorites) {
      // Get post details for each favorite
      const favoriteIds = response.data.favorites.map(f => f.post_id);
      favoritesCount.value = favoriteIds.length;
      
      if (favoriteIds.length === 0) {
        favorites.value = [];
        return;
      }
      
      // Batch fetch posts
      const postsResponse = await Promise.all(
        favoriteIds.map(id => postsApi.get(id))
      );
      
      favorites.value = postsResponse
        .filter(r => r.success && r.data)
        .map(r => r.data);
    }
  } catch (err) {
    console.error('Failed to load favorites:', err);
  } finally {
    loadingFavorites.value = false;
  }
};

const handleLogout = () => {
  if (confirm('Are you sure you want to log out?')) {
    logout();
  }
};

const handlePostDeleted = (postId) => {
  const index = posts.value.findIndex(p => p._id === postId);
  if (index > -1) {
    posts.value.splice(index, 1);
    postsCount.value = Math.max(0, postsCount.value - 1);
  }
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

const editCorner = (corner) => {
  router.push({
    path: `/edit-corner/${corner._id}`
  });
};

const getMediaUrl = (fileId) => {
  return mediaApi.getUrl(fileId);
};

onMounted(() => {
  loadUserProfile();
  if (isSelf.value) {
    loadUserCorners(currentUser.value.id);
  }
});

// Watch for route changes to reload profile (including when returning from other pages)
watch(() => route.path, (newPath, oldPath) => {
  if (newPath !== oldPath && newPath.startsWith('/profile')) {
    // Reset state
    user.value = null;
    posts.value = [];
    corners.value = [];
    followingList.value = [];
    followersList.value = [];
    favorites.value = [];
    followingCount.value = 0;
    followersCount.value = 0;
    postsCount.value = 0;
    cornersCount.value = 0;
    favoritesCount.value = 0;
    activeTab.value = 'posts';
    
    // Load fresh profile data
    loadUserProfile();
    const userId = route.params.userId || currentUser.value?.id;
    if (userId && (!route.params.userId || currentUser.value?.id === route.params.userId)) {
      loadUserCorners(userId);
    }
  }
});

const goToProfile = (userId) => {
  router.push({
    path: `/profile/${userId}`
  });
};
</script>

<style scoped>
.user-profile-view {
  height: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.profile-container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initial {
  color: white;
  font-weight: bold;
  font-size: 32px;
}

.user-info {
  flex: 1;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.user-name-row h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.username-hint {
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.edit-btn {
  padding: 6px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.edit-btn:hover {
  background: #66b1ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-item.clickable {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-item.clickable:hover {
  opacity: 0.7;
}

.stat-number {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.stat-icon {
  font-size: 20px;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.follow-section {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.logout-btn {
  margin-left: auto;
  padding: 6px 16px;
  background: #f56c6c;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: #e63946;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.3);
}

.interests-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.interests-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  display: inline-block;
  padding: 6px 14px;
  background: #409eff;
  color: white;
  border-radius: 16px;
  font-size: 13px;
}

/* Tabs */
.tabs-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.tabs {
  display: flex;
  gap: 4px;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 10px;
}

.tab-btn {
  flex: 1;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: white;
  color: #333;
}

.tab-btn.active {
  background: white;
  color: #409eff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.posts-section {
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.corners-section {
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.posts-section h3,
.corners-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.corners-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.corner-item {
  background: #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.corner-item:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
  transform: translateY(-2px);
}

.corner-images {
  width: 100%;
  height: 180px;
  background: #e0e0e0;
  overflow: hidden;
}

.corner-images img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.corner-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.placeholder-icon {
  font-size: 48px;
}

.corner-info {
  padding: 16px;
}

.corner-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #333;
}

.corner-description {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.corner-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.corner-posts {
  font-size: 12px;
  color: #999;
}

.edit-corner-btn {
  padding: 6px 12px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.edit-corner-btn:hover {
  background: #66b1ff;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
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

.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: #999;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.users-section,
.favorites-section {
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.users-section h3,
.favorites-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.user-item:hover {
  background: #e9ecef;
  transform: translateX(4px);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 20px;
  flex-shrink: 0;
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

/* Mobile Responsive Styles */
@media (max-width: 600px) {
  .user-profile-view {
    padding: 10px;
  }

  .profile-container {
    padding: 16px;
    border-radius: 8px;
  }

  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 16px;
  }

  .avatar {
    width: 64px;
    height: 64px;
  }

  .avatar-initial {
    font-size: 26px;
  }

  .user-name-row {
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  .user-name-row h1 {
    font-size: 20px;
  }

  .action-buttons {
    width: 100%;
    justify-content: center;
  }

  .edit-btn,
  .logout-btn {
    flex: 1;
    padding: 10px;
  }

  .user-info {
    width: 100%;
  }

  .stats {
    justify-content: space-around;
    gap: 12px;
  }

  .stat-number {
    font-size: 18px;
  }

  .stat-label {
    font-size: 11px;
  }

  .interests-section {
    padding: 14px;
  }

  .interests-section h3 {
    font-size: 14px;
  }

  .tag-chip {
    padding: 4px 10px;
    font-size: 12px;
  }

  .tabs {
    flex-wrap: wrap;
    gap: 4px;
  }

  .tab-btn {
    padding: 10px 12px;
    font-size: 13px;
    min-width: calc(33% - 4px);
  }

  .posts-section h3,
  .corners-section h3,
  .users-section h3,
  .favorites-section h3 {
    font-size: 16px;
  }

  .corners-list {
    grid-template-columns: 1fr;
  }

  .corner-images {
    height: 140px;
  }

  .corner-info {
    padding: 12px;
  }

  .corner-info h4 {
    font-size: 15px;
  }

  .user-avatar {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }

  .user-item {
    padding: 10px 12px;
  }

  .user-name {
    font-size: 14px;
  }
}
</style>

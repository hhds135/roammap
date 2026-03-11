<template>
  <div class="user-profile-view">
    <div class="profile-container">
      <!-- User Info Header -->
      <div class="profile-header">
        <div class="avatar">{{ user?.username?.charAt(0).toUpperCase() || 'U' }}</div>
        <div class="user-info">
          <h1>{{ user?.username || 'Unknown User' }}</h1>
          <div class="stats">
            <div class="stat-item">
              <span class="stat-number">{{ followingCount }}</span>
              <span class="stat-label">Following</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ followersCount }}</span>
              <span class="stat-label">Followers</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ postsCount }}</span>
              <span class="stat-label">Posts</span>
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

      <!-- User's Posts -->
      <div class="posts-section">
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
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { followsApi } from '../api/follows';
import { postsApi } from '../api/posts';
import { usersApi } from '../api/users';
import PostCard from '../components/Feed/PostCard.vue';
import FollowButton from '../components/User/FollowButton.vue';

const route = useRoute();
const { user: currentUser } = useAuth();

const user = ref(null);
const posts = ref([]);
const followingCount = ref(0);
const followersCount = ref(0);
const postsCount = ref(0);
const loading = ref(false);

const isSelf = computed(() => {
  return currentUser.value?.id === route.params.userId || false;
});

const loadUserProfile = async () => {
  const userId = route.params.userId;

  if (!userId) {
    // Show current user's profile
    if (currentUser.value) {
      user.value = currentUser.value;
      await loadUserStats(currentUser.value.id);
      await loadUserPosts(currentUser.value.id);
    }
    return;
  }

  // Show other user's profile
  try {
    // Load user interests
    const interestsResponse = await usersApi.getInterests(userId);
    if (interestsResponse.success && interestsResponse.data) {
      user.value = {
        id: userId,
        username: interestsResponse.data.username,
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
    const [following, followers, postsResponse] = await Promise.all([
      followsApi.getFollowing(userId, { limit: 1 }),
      followsApi.getFollowers(userId, { limit: 1 }),
      postsApi.list({ user_id: userId, limit: 1 })
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

onMounted(() => {
  loadUserProfile();
});
</script>

<style scoped>
.user-profile-view {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 32px;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
}

.user-info h1 {
  margin: 0 0 16px 0;
  font-size: 24px;
  color: #333;
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

.stat-number {
  font-size: 20px;
  font-weight: 600;
  color: #333;
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

.posts-section {
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.posts-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
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
</style>
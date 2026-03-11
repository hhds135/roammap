<template>
  <button
    v-if="!isSelf"
    @click="handleToggleFollow"
    :disabled="loading"
    :class="['follow-button', { following: isFollowing }]"
  >
    {{ loading ? 'Processing...' : (isFollowing ? 'Following' : 'Follow') }}
  </button>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuth } from '../../composables/useAuth';
import { followsApi } from '../../api/follows';

const props = defineProps({
  targetUserId: {
    type: String,
    required: true
  }
});

const { user: currentUser } = useAuth();
const isFollowing = ref(false);
const loading = ref(false);

const isSelf = computed(() => {
  return currentUser.value?.id === props.targetUserId;
});

const loadFollowStatus = async () => {
  try {
    const response = await followsApi.getStatus(props.targetUserId);
    if (response.success && response.data) {
      isFollowing.value = response.data.is_following;
    }
  } catch (err) {
    console.error('Failed to load follow status', err);
  }
};

const handleToggleFollow = async () => {
  loading.value = true;

  try {
    if (isFollowing.value) {
      await followsApi.unfollow(props.targetUserId);
      isFollowing.value = false;
    } else {
      await followsApi.follow(props.targetUserId);
      isFollowing.value = true;
    }
  } catch (err) {
    console.error('Failed to toggle follow', err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (!isSelf.value) {
    loadFollowStatus();
  }
});
</script>

<style scoped>
.follow-button {
  padding: 8px 20px;
  border: 1px solid #409eff;
  background: white;
  color: #409eff;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.follow-button:hover {
  background: #409eff;
  color: white;
}

.follow-button.following {
  background: #409eff;
  color: white;
}

.follow-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
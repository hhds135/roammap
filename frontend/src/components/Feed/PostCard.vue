<template>
  <div class="post-card">
    <div class="post-header">
      <div class="user-info">
        <div class="avatar">{{ username.charAt(0).toUpperCase() }}</div>
        <div class="user-details">
          <span class="username">{{ username }}</span>
          <span class="timestamp">{{ formattedTime }}</span>
        </div>
      </div>
    </div>

    <h3 class="post-title">{{ post.title }}</h3>
    <p v-if="post.description" class="post-description">{{ post.description }}</p>

    <!-- 媒体内容 -->
    <div class="post-media">
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

    <!-- 地点标签 -->
    <div v-if="post.corners && post.corners.length > 0" class="post-corners">
      <span v-for="corner in post.corners" :key="corner._id" class="corner-tag">
        @{{ corner.name }}
      </span>
    </div>

    <!-- 标签 -->
    <div v-if="post.tags && post.tags.length > 0" class="post-tags">
      <span v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</span>
    </div>

    <!-- 统计信息 -->
    <div class="post-stats">
      <span class="stat">👍 {{ post.stats?.likes_count || 0 }}</span>
      <span class="stat">💬 {{ post.stats?.comments_count || 0 }}</span>
      <span class="stat">⭐ {{ post.stats?.favorites_count || 0 }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { mediaApi } from '../../api/media';
import { formatters } from '../../utils/format';

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
});

const username = computed(() => props.post.username || 'Unknown User');

const formattedTime = computed(() => {
  return formatters.formatRelativeTime(props.post.created_at);
});

const getMediaUrl = (fileId) => {
  return mediaApi.getUrl(fileId);
};
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
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
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
}

.post-media img,
.post-media video {
  width: 100%;
  display: block;
}

.post-corners {
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
}

.post-tags {
  margin-bottom: 12px;
}

.tag {
  display: inline-block;
  padding: 4px 12px;
  background: #f5f5f5;
  color: #666;
  border-radius: 16px;
  font-size: 14px;
  margin-right: 8px;
  margin-bottom: 8px;
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
</style>
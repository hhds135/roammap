<template>
  <div class="comment-list">
    <div v-if="loading" class="loading">Loading...</div>
    
    <div v-else-if="comments.length === 0" class="no-comments">
      No comments yet, be the first to comment!
    </div>
    
    <div v-else class="comments-container">
      <div 
        v-for="comment in comments" 
        :key="comment._id" 
        class="comment-item"
      >
        <div class="comment-avatar">
          {{ comment.username ? comment.username.charAt(0).toUpperCase() : 'U' }}
        </div>
        
        <div class="comment-content-wrapper">
          <div class="comment-header">
            <span class="comment-username">{{ comment.username || 'Anonymous' }}</span>
            <span class="comment-time">{{ formatters.formatRelativeTime(comment.created_at) }}</span>
          </div>
          
          <div class="comment-text">{{ comment.content }}</div>
          
          <div v-if="canDelete(comment)" class="comment-actions">
            <button 
              @click="handleDelete(comment._id)" 
              class="delete-btn"
              :disabled="deleting"
            >
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { commentsApi } from '../../api/comments';
import { useAuth } from '../../composables/useAuth';
import { formatters } from '../../utils/format';

const props = defineProps({
  postId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['commentDeleted', 'commentCountChanged']);

const { user } = useAuth();

const comments = ref([]);
const loading = ref(true);
const deleting = ref(false);

const loadComments = async () => {
  loading.value = true;
  try {
    const response = await commentsApi.getPostComments(props.postId);
    if (response.success && response.data) {
      comments.value = response.data.comments || [];
      emit('commentCountChanged', response.data.total || 0);
    }
  } catch (error) {
    console.error('Failed to load comments:', error);
  } finally {
    loading.value = false;
  }
};

const canDelete = (comment) => {
  return user.value && user.value._id === comment.user_id;
};

const handleDelete = async (commentId) => {
  if (!confirm('Are you sure you want to delete this comment?')) {
    return;
  }
  
  deleting.value = true;
  try {
    const response = await commentsApi.delete(commentId);
    if (response.success) {
      comments.value = comments.value.filter(c => c._id !== commentId);
      emit('commentDeleted');
      emit('commentCountChanged', comments.value.length);
    }
  } catch (error) {
    console.error('Failed to delete comment:', error);
    alert('Failed to delete comment');
  } finally {
    deleting.value = false;
  }
};

const addComment = (comment) => {
  comments.value.unshift(comment);
  emit('commentCountChanged', comments.value.length);
};

onMounted(() => {
  loadComments();
});

defineExpose({
  addComment,
  loadComments
});
</script>

<style scoped>
.comment-list {
  max-height: 400px;
  overflow-y: auto;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.no-comments {
  text-align: center;
  padding: 20px;
  color: #999;
}

.comments-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-item {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: #f8f8f8;
  border-radius: 8px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  min-width: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.comment-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-username {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-text {
  font-size: 14px;
  color: #555;
  line-height: 1.5;
  word-break: break-word;
}

.comment-actions {
  margin-top: 4px;
  display: flex;
  justify-content: flex-end;
}

.delete-btn {
  padding: 4px 12px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-btn:hover:not(:disabled) {
  background: #fee;
  border-color: #fcc;
  color: #c33;
}

.delete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
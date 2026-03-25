<template>
  <div class="comment-form">
    <textarea
      v-model="content"
      placeholder="Write your comment..."
      class="comment-input"
      :disabled="submitting"
      @keydown.enter.prevent="handleSubmit"
    ></textarea>
    
    <div class="comment-form-actions">
      <button
        @click="handleSubmit"
        class="submit-btn"
        :disabled="!canSubmit || submitting"
      >
        {{ submitting ? 'Sending...' : 'Send' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { commentsApi } from '../../api/comments';
import { useAuth } from '../../composables/useAuth';

const props = defineProps({
  postId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['commentAdded']);

const { user } = useAuth();

const content = ref('');
const submitting = ref(false);

const canSubmit = computed(() => {
  return content.value.trim().length > 0 && user.value && !submitting.value;
});

const handleSubmit = async () => {
  if (!canSubmit.value) {
    return;
  }

  const trimmedContent = content.value.trim();
  if (!trimmedContent) {
    return;
  }

  submitting.value = true;
  try {
    const response = await commentsApi.add(props.postId, trimmedContent);
    if (response.success && response.data) {
      const newComment = {
        ...response.data,
        _id: response.data._id || Date.now().toString(),
        // Ensure these fields are at the top level for CommentList compatibility
        username: response.data.username || response.data.user?.username,
        user_id: response.data.user_id || response.data.user?._id
      };
      emit('commentAdded', newComment);
      content.value = '';
    } else {
      alert('Failed to send comment');
    }
  } catch (error) {
    console.error('Failed to add comment:', error);
    alert('Failed to send comment');
  } finally {
    submitting.value = false;
  }
};

const focus = () => {
  const textarea = document.querySelector('.comment-input');
  if (textarea) {
    textarea.focus();
  }
};

defineExpose({
  focus
});
</script>

<style scoped>
.comment-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.comment-input {
  width: 100%;
  min-height: 80px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.comment-input:focus {
  outline: none;
  border-color: #667eea;
}

.comment-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.comment-form-actions {
  display: flex;
  justify-content: flex-end;
}

.submit-btn {
  padding: 8px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>
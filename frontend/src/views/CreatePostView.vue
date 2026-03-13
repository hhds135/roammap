<template>
  <div class="create-post-view">
    <div class="create-container">
      <h1>Create Post</h1>

      <form @submit.prevent="handleSubmit" class="create-form">
        <!-- Title -->
        <div class="form-group">
          <label for="title">Title *</label>
          <input
            id="title"
            v-model="formData.title"
            type="text"
            placeholder="Give your post a title"
            required
            maxlength="100"
          />
        </div>

        <!-- Description -->
        <div class="form-group">
          <label for="description">Description</label>
          <textarea
            id="description"
            v-model="formData.description"
            placeholder="Tell your story..."
            rows="4"
            maxlength="500"
          ></textarea>
          <div class="char-count">{{ formData.description.length }}/500</div>
        </div>

        <!-- Media Upload -->
        <div class="form-group">
          <label>Media *</label>
          <MediaUploader ref="mediaUploader" />
        </div>

        <!-- Corners -->
        <div class="form-group">
          <CornerSelector v-model="formData.corners" />
          <p v-if="formData.corners.length >= 2" class="route-hint">
            🛤️ These {{ formData.corners.length }} locations will form a route
          </p>
        </div>

        <!-- Tags -->
        <div class="form-group">
          <label>Tags</label>
          <div class="tags-input">
            <input
              v-model="newTag"
              type="text"
              placeholder="Add a tag and press Enter"
              @keyup.enter="addTag"
            />
            <button type="button" @click="addTag" :disabled="!newTag.trim()">Add</button>
          </div>
          <div class="tags-list">
            <span
              v-for="(tag, idx) in formData.tags"
              :key="idx"
              class="tag-chip"
            >
              #{{ tag }}
              <button type="button" @click="removeTag(idx)" class="remove">×</button>
            </span>
          </div>
        </div>

        <!-- Visibility -->
        <div class="form-group">
          <label>Visibility</label>
          <div class="visibility-options">
            <label
              v-for="option in visibilityOptions"
              :key="option.value"
              :class="['visibility-option', { active: formData.visibility === option.value }]"
            >
              <input
                type="radio"
                v-model="formData.visibility"
                :value="option.value"
              />
              <span class="visibility-icon">{{ option.icon }}</span>
              <span class="visibility-label">{{ option.label }}</span>
              <span class="visibility-desc">{{ option.desc }}</span>
            </label>
          </div>
        </div>

        <!-- Actions -->
        <div class="form-actions">
          <button type="button" @click="handleCancel" class="btn-cancel">Cancel</button>
          <button type="submit" class="btn-submit" :disabled="loading || !canSubmit">
            {{ loading ? 'Creating...' : 'Create Post' }}
          </button>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { postsApi } from '../api/posts';
import MediaUploader from '../components/Media/MediaUploader.vue';
import CornerSelector from '../components/Corner/CornerSelector.vue';

const router = useRouter();
const mediaUploader = ref(null);

const formData = ref({
  title: '',
  description: '',
  media_type: 'image',
  media_files: [],
  corners: [],
  tags: [],
  visibility: 'public'
});

const newTag = ref('');
const loading = ref(false);
const error = ref(null);

const visibilityOptions = [
  { value: 'public', label: 'Public', icon: '🌍', desc: 'Everyone can see' },
  { value: 'followers', label: 'Followers', icon: '👥', desc: 'Only followers can see' },
  { value: 'private', label: 'Private', icon: '🔒', desc: 'Only you can see' }
];

const canSubmit = computed(() => {
  return formData.value.title.trim() !== '' && !loading.value;
});

const addTag = () => {
  const trimmedTag = newTag.value.trim();
  if (!trimmedTag) return;
  if (formData.value.tags.includes(trimmedTag)) {
    alert('Tag already exists');
    return;
  }
  if (formData.value.tags.length >= 10) {
    alert('Maximum 10 tags allowed');
    return;
  }
  formData.value.tags.push(trimmedTag);
  newTag.value = '';
};

const removeTag = (index) => {
  formData.value.tags.splice(index, 1);
};

const handleSubmit = async () => {
  if (!canSubmit.value) return;

  // Upload media first
  let uploadedFileIds = [];
  if (mediaUploader.value) {
    try {
      uploadedFileIds = await mediaUploader.value.uploadAll();
    } catch (err) {
      error.value = 'Failed to upload media files';
      return;
    }
  }

  if (uploadedFileIds.length === 0) {
    error.value = 'Please add at least one media file';
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const postData = {
      title: formData.value.title.trim(),
      description: formData.value.description.trim(),
      media_type: mediaUploader.value.selectedType || 'image',
      media_files: uploadedFileIds,
      corner_ids: formData.value.corners.map(c => c._id),
      tags: formData.value.tags,
      visibility: formData.value.visibility
    };

    // Auto-create route if 2+ corners are selected
    // The corners order defines the route sequence
    if (formData.value.corners.length >= 2) {
      postData.route = {
        corner_ids: formData.value.corners.map(c => c._id)
      };
    }

    const response = await postsApi.create(postData);

    if (response.success && response.data) {
      router.push('/feed');
    } else {
      error.value = response.error?.message || 'Failed to create post';
    }
  } catch (err) {
    error.value = err.error?.message || 'Failed to create post';
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  router.back();
};
</script>

<style scoped>
.create-post-view {
  height: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.create-container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.create-container h1 {
  margin-bottom: 24px;
  color: #333;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.route-hint {
  margin-top: 8px;
  padding: 10px 14px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
}

.form-group input[type="text"]:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #409eff;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
}

.tags-input {
  display: flex;
  gap: 10px;
}

.tags-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.tags-input input:focus {
  outline: none;
  border-color: #409eff;
}

.tags-input button {
  padding: 10px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.tags-input button:hover:not(:disabled) {
  background: #66b1ff;
}

.tags-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: #f5f5f5;
  border-radius: 16px;
  font-size: 13px;
}

.tag-chip .remove {
  margin-left: 6px;
  padding: 0 2px;
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.tag-chip .remove:hover {
  color: #f56c6c;
}

.visibility-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.visibility-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.visibility-option:hover {
  border-color: #409eff;
}

.visibility-option.active {
  border-color: #409eff;
  background: #e3f2fd;
}

.visibility-option input[type="radio"] {
  display: none;
}

.visibility-icon {
  font-size: 24px;
}

.visibility-label {
  font-weight: 600;
  color: #333;
}

.visibility-desc {
  font-size: 13px;
  color: #999;
  margin-left: auto;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn-cancel {
  flex: 1;
  padding: 14px;
  background: white;
  color: #666;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel:hover {
  border-color: #409eff;
  color: #409eff;
}

.btn-submit {
  flex: 2;
  padding: 14px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.btn-submit:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  padding: 12px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 8px;
  text-align: center;
  font-size: 14px;
}
</style>
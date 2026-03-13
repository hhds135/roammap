<template>
  <div class="edit-corner-view">
    <div class="edit-container">
      <h1>Edit Corner</h1>

      <form @submit.prevent="handleSubmit" class="edit-form">
        <!-- Name -->
        <div class="form-group">
          <label for="name">Corner Name *</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            placeholder="Enter corner name"
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
            placeholder="Describe this corner..."
            rows="4"
            maxlength="500"
          ></textarea>
          <div class="char-count">{{ formData.description.length }}/500</div>
        </div>

        <!-- Address -->
        <div class="form-group">
          <label for="address">Address</label>
          <input
            id="address"
            v-model="formData.address"
            type="text"
            placeholder="Enter address (optional)"
            maxlength="200"
          />
        </div>

        <!-- Current Images -->
        <div v-if="currentImages.length > 0" class="form-group">
          <label>Current Images</label>
          <div class="current-images-grid">
            <div
              v-for="(imageId, idx) in currentImages"
              :key="idx"
              class="current-image-item"
            >
              <img :src="getMediaUrl(imageId)" :alt="`Image ${idx + 1}`" />
              <button 
                type="button" 
                @click="removeCurrentImage(idx)" 
                class="remove-image-btn"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <!-- Upload New Images -->
        <div class="form-group">
          <label>Add New Images</label>
          <MediaUploader
            ref="mediaUploader"
            :media-type="'image'"
            :max-files="5 - currentImages.length"
          />
          <p class="form-hint">Maximum 5 images total ({{ currentImages.length }} currently, {{ 5 - currentImages.length }} remaining)</p>
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

        <!-- Actions -->
        <div class="form-actions">
          <button type="button" @click="handleCancel" class="btn-cancel">Cancel</button>
          <button type="submit" class="btn-submit" :disabled="loading || !canSubmit">
            {{ loading ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { cornersApi } from '../api/corners';
import { mediaApi } from '../api/media';
import MediaUploader from '../components/Media/MediaUploader.vue';

const router = useRouter();
const route = useRoute();

const formData = ref({
  name: '',
  description: '',
  address: '',
  tags: [],
  images: []
});

const newTag = ref('');
const loading = ref(false);
const error = ref(null);
const currentImages = ref([]);
const mediaUploader = ref(null);

const canSubmit = computed(() => {
  return (
    formData.value.name.trim() !== '' &&
    !loading.value
  );
});

const loadCorner = async () => {
  const cornerId = route.params.cornerId;
  loading.value = true;
  error.value = null;

  try {
    const response = await cornersApi.get(cornerId);
    if (response.success && response.data) {
      const corner = response.data;
      formData.value = {
        name: corner.name,
        description: corner.description || '',
        address: corner.address || '',
        tags: corner.tags || [],
        images: corner.images || []
      };
      currentImages.value = [...(corner.images || [])];
    }
  } catch (err) {
    error.value = 'Failed to load corner';
  } finally {
    loading.value = false;
  }
};

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

const removeCurrentImage = (index) => {
  if (confirm('Are you sure you want to delete this image?')) {
    currentImages.value.splice(index, 1);
  }
};

const handleSubmit = async () => {
  if (!canSubmit.value) return;

  loading.value = true;
  error.value = null;

  try {
    // Upload new images first
    let uploadedImageIds = [];
    if (mediaUploader.value && mediaUploader.value.hasFiles()) {
      uploadedImageIds = await mediaUploader.value.uploadAll();
    }

    // Combine current and new images
    const allImages = [...currentImages.value, ...uploadedImageIds];

    const cornerId = route.params.cornerId;
    const response = await cornersApi.update(cornerId, {
      name: formData.value.name.trim(),
      description: formData.value.description.trim(),
      address: formData.value.address.trim(),
      tags: formData.value.tags,
      images: allImages
    });

    if (response.success) {
      alert('Corner updated successfully!');
      router.push('/profile');
    } else {
      error.value = response.error?.message || 'Failed to update corner';
    }
  } catch (err) {
    error.value = err.error?.message || 'Failed to update corner';
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  router.back();
};

const getMediaUrl = (fileId) => {
  return mediaApi.getUrl(fileId);
};

onMounted(() => {
  loadCorner();
});
</script>

<style scoped>
.edit-corner-view {
  height: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.edit-container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.edit-container h1 {
  margin-bottom: 24px;
  color: #333;
}

.edit-form {
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

.current-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
}

.current-image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.current-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  background: rgba(244, 67, 54, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
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

.form-hint {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #999;
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
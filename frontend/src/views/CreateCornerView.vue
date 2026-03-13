<template>
  <div class="create-corner-view">
    <div class="create-container">
      <h1>Create Corner</h1>

      <form @submit.prevent="handleSubmit" class="create-form">
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

        <!-- Location -->
        <div class="form-group">
          <label>Location</label>
          <div class="location-display">
            <span class="location-icon">📍</span>
            <span class="location-coords">
              {{ formData.latitude ? formData.latitude.toFixed(6) : '-' }}, 
              {{ formData.longitude ? formData.longitude.toFixed(6) : '-' }}
            </span>
          </div>
          <p class="location-hint">Location selected from map</p>
          <input type="hidden" v-model="formData.latitude" />
          <input type="hidden" v-model="formData.longitude" />
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

        <!-- Images -->
        <div class="form-group">
          <label>Images</label>
          <MediaUploader
            ref="mediaUploader"
            :media-type="'image'"
            :max-files="5"
          />
          <p class="form-hint">Upload up to 5 images to showcase this corner</p>
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
            {{ loading ? 'Creating...' : 'Create Corner' }}
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
import MediaUploader from '../components/Media/MediaUploader.vue';

const router = useRouter();
const route = useRoute();

const formData = ref({
  name: '',
  description: '',
  latitude: '',
  longitude: '',
  address: '',
  tags: [],
  images: []
});

const newTag = ref('');
const loading = ref(false);
const error = ref(null);
const mediaUploader = ref(null);

// Initialize form with location from route params
onMounted(() => {
  const lat = route.query.lat;
  const lng = route.query.lng;
  
  if (lat && lng) {
    formData.value.latitude = parseFloat(lat);
    formData.value.longitude = parseFloat(lng);
  }
});

const canSubmit = computed(() => {
  return (
    formData.value.name.trim() !== '' &&
    formData.value.latitude !== '' &&
    formData.value.longitude !== '' &&
    !loading.value
  );
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
  console.log('[DEBUG] handleSubmit called');
  console.log('[DEBUG] canSubmit:', canSubmit.value);
  console.log('[DEBUG] formData:', formData.value);

  if (!canSubmit.value) {
    console.log('[DEBUG] Cannot submit - form validation failed');
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    // Upload images first
    console.log('[DEBUG] Checking for images to upload...');
    let uploadedImageIds = [];
    if (mediaUploader.value && mediaUploader.value.hasFiles()) {
      console.log('[DEBUG] Uploading images...');
      uploadedImageIds = await mediaUploader.value.uploadAll();
      console.log('[DEBUG] Uploaded images:', uploadedImageIds);
    } else {
      console.log('[DEBUG] No images to upload');
    }

    console.log('[DEBUG] Preparing to create corner with data:', {
      name: formData.value.name.trim(),
      description: formData.value.description.trim(),
      latitude: parseFloat(formData.value.latitude),
      longitude: parseFloat(formData.value.longitude),
      address: formData.value.address.trim(),
      tags: formData.value.tags,
      images: uploadedImageIds
    });

    const response = await cornersApi.create({
      name: formData.value.name.trim(),
      description: formData.value.description.trim(),
      latitude: parseFloat(formData.value.latitude),
      longitude: parseFloat(formData.value.longitude),
      address: formData.value.address.trim(),
      tags: formData.value.tags,
      images: uploadedImageIds
    });

    console.log('[DEBUG] API response:', response);

    if (response.success && response.data) {
      console.log('[DEBUG] Corner created successfully:', response.data);
      // Check if we should redirect to create post
      const redirectToPost = route.query.redirect_to_post === 'true';

      if (redirectToPost) {
        // Redirect to create post with the new corner pre-selected
        router.push({
          path: '/create',
          query: { corner_id: response.data._id }
        });
      } else {
        alert('Corner created successfully!');
        router.push('/map');
      }
    } else {
      console.error('[DEBUG] API returned error:', response);
      error.value = response.error?.message || 'Failed to create corner';
    }
  } catch (err) {
    console.error('[DEBUG] Exception caught:', err);
    console.error('[DEBUG] Error details:', {
      message: err.message,
      stack: err.stack,
      response: err.response,
      request: err.request
    });
    error.value = err.error?.message || err.message || 'Failed to create corner';
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  router.back();
};
</script>

<style scoped>
.create-corner-view {
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
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
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

.form-group input[type="text"],
.form-group input[type="number"],
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
.form-group input[type="number"]:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #409eff;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
}

.location-display {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #e8f5e9;
  border-radius: 8px;
  border: 2px solid #4caf50;
}

.location-icon {
  font-size: 24px;
}

.location-coords {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #2e7d32;
}

.location-hint {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: #666;
  font-style: italic;
}

/* Tags Input */

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
<template>
  <div class="edit-profile-view">
    <div class="edit-container">
      <div class="header">
        <button @click="goBack" class="back-btn">← Back</button>
        <h1>Edit Profile</h1>
      </div>

      <form @submit.prevent="handleSubmit" class="edit-form">
        <!-- Avatar Section -->
        <div class="avatar-section">
          <div class="avatar-preview" :style="avatarStyle" @click="triggerFileInput">
            <img v-if="avatarPreview" :src="avatarPreview" alt="Avatar" @error="handleAvatarError" />
            <span v-else class="avatar-placeholder">
              {{ displayInitial }}
            </span>
            <div class="avatar-overlay">
              <span class="overlay-text">{{ uploadingAvatar ? 'Uploading...' : 'Change' }}</span>
            </div>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            @change="handleAvatarChange"
            style="display: none"
          />
          <div class="avatar-info">
            <label>Avatar</label>
            <p class="hint">Click to upload a new avatar (max 5MB)</p>
            <p class="hint">Supported: PNG, JPG, GIF, WebP</p>
          </div>
        </div>

        <!-- Nickname Section -->
        <div class="form-group">
          <label>Nickname</label>
          <input
            v-model="formData.nickname"
            type="text"
            placeholder="Enter your display name"
            maxlength="30"
          />
          <div class="input-meta">
            <span class="char-count">{{ formData.nickname?.length || 0 }}/30</span>
          </div>
        </div>

        <!-- Username (Read-only) -->
        <div class="form-group">
          <label>Username</label>
          <input
            :value="user?.username"
            type="text"
            disabled
            class="readonly"
          />
          <p class="hint">Username cannot be changed</p>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Success Message -->
        <div v-if="success" class="success-message">
          Profile updated successfully!
        </div>

        <!-- Actions -->
        <div class="actions">
          <button type="button" @click="goBack" class="btn-cancel">
            Cancel
          </button>
          <button type="submit" class="btn-save" :disabled="saving || uploadingAvatar">
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { usersApi } from '../api/users';
import { mediaApi } from '../api/media';

const router = useRouter();
const { user, updateUser } = useAuth();

const formData = ref({
  nickname: '',
  avatar_id: ''
});

const avatarPreview = ref('');
const avatarError = ref(false);
const uploadingAvatar = ref(false);
const saving = ref(false);
const error = ref('');
const success = ref(false);
const fileInput = ref(null);

const displayInitial = computed(() => {
  return formData.value.nickname?.charAt(0)?.toUpperCase() || 
         user.value?.username?.charAt(0)?.toUpperCase() || 'U';
});

const avatarStyle = computed(() => {
  if (avatarError.value) {
    return {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    };
  }
  return {};
});

const handleAvatarError = () => {
  avatarError.value = true;
};

const triggerFileInput = () => {
  if (!uploadingAvatar.value) {
    fileInput.value?.click();
  }
};

const handleAvatarChange = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // Validate file type
  const allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    error.value = 'Invalid file type. Please use PNG, JPG, GIF, or WebP.';
    return;
  }

  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    error.value = 'File too large. Maximum size is 5MB.';
    return;
  }

  error.value = '';
  avatarError.value = false;
  uploadingAvatar.value = true;

  try {
    // Create preview URL
    avatarPreview.value = URL.createObjectURL(file);

    // Upload to server
    const response = await mediaApi.upload(file, 'image');
    
    if (response.success && response.data?.file_id) {
      formData.value.avatar_id = response.data.file_id;
    } else {
      error.value = 'Failed to upload avatar';
      avatarPreview.value = '';
    }
  } catch (err) {
    error.value = err.message || 'Failed to upload avatar';
    avatarPreview.value = '';
  } finally {
    uploadingAvatar.value = false;
    // Reset file input
    event.target.value = '';
  }
};

const goBack = () => {
  router.back();
};

const handleSubmit = async () => {
  error.value = '';
  success.value = false;

  // Validate nickname
  if (!formData.value.nickname?.trim()) {
    error.value = 'Nickname cannot be empty';
    return;
  }

  if (formData.value.nickname.length > 30) {
    error.value = 'Nickname cannot exceed 30 characters';
    return;
  }

  saving.value = true;

  try {
    const updateData = {
      nickname: formData.value.nickname.trim()
    };

    // Only include avatar_id if it was changed
    if (formData.value.avatar_id && formData.value.avatar_id !== user.value?.avatar_id) {
      updateData.avatar_id = formData.value.avatar_id;
    }

    const response = await usersApi.updateProfile(user.value.id, updateData);

    if (response.success) {
      success.value = true;
      // Update local user state
      updateUser(response.data);
      
      setTimeout(() => {
        router.push('/profile');
      }, 1000);
    } else {
      error.value = response.error || 'Failed to update profile';
    }
  } catch (err) {
    error.value = err.message || 'Failed to update profile';
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  if (user.value) {
    formData.value.nickname = user.value.nickname || user.value.username || '';
    formData.value.avatar_id = user.value.avatar_id || '';
    
    // Set avatar preview if exists
    if (user.value.avatar_id) {
      avatarPreview.value = mediaApi.getUrl(user.value.avatar_id);
    }
  }
});
</script>

<style scoped>
.edit-profile-view {
  height: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.edit-container {
  max-width: 500px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.back-btn {
  background: none;
  border: none;
  color: #409eff;
  font-size: 15px;
  cursor: pointer;
  padding: 8px 0;
}

.back-btn:hover {
  color: #66b1ff;
}

.header h1 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  color: white;
  font-weight: bold;
  font-size: 40px;
}

.avatar-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  text-align: center;
  padding: 6px 0;
  opacity: 0;
  transition: opacity 0.3s;
}

.avatar-preview:hover .avatar-overlay {
  opacity: 1;
}

.overlay-text {
  font-size: 12px;
  font-weight: 500;
}

.avatar-info {
  flex: 1;
}

.avatar-info label {
  display: block;
  font-weight: 600;
  color: #333;
  font-size: 14px;
  margin-bottom: 8px;
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

.form-group input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.form-group input.readonly {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.input-meta {
  display: flex;
  justify-content: flex-end;
}

.char-count {
  font-size: 12px;
  color: #999;
}

.hint {
  margin: 0;
  font-size: 12px;
  color: #999;
  font-style: italic;
}

.error-message {
  padding: 12px 16px;
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 8px;
  color: #f56c6c;
  font-size: 14px;
}

.success-message {
  padding: 12px 16px;
  background: #f0f9eb;
  border: 1px solid #c2e7b0;
  border-radius: 8px;
  color: #67c23a;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn-cancel {
  flex: 1;
  padding: 12px;
  background: white;
  color: #666;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel:hover {
  border-color: #409eff;
  color: #409eff;
}

.btn-save {
  flex: 1;
  padding: 12px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.btn-save:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Mobile Responsive */
@media (max-width: 600px) {
  .edit-profile-view {
    padding: 10px;
  }

  .edit-container {
    padding: 16px;
  }

  .avatar-section {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .avatar-preview {
    width: 120px;
    height: 120px;
  }

  .avatar-placeholder {
    font-size: 48px;
  }

  .avatar-info {
    width: 100%;
  }
}
</style>
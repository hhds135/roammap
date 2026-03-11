<template>
  <div class="media-uploader">
    <div class="media-type-selector">
      <button
        v-for="type in mediaTypes"
        :key="type.value"
        :class="['type-button', { active: selectedType === type.value }]"
        @click="selectType(type.value)"
      >
        <span class="type-icon">{{ type.icon }}</span>
        <span class="type-label">{{ type.label }}</span>
      </button>
    </div>

    <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
      <input
        ref="fileInput"
        type="file"
        :accept="selectedType === 'image' ? 'image/*' : 'video/*'"
        multiple
        @change="handleFileSelect"
        style="display: none"
      />
      <div v-if="files.length === 0" class="upload-placeholder">
        <div class="upload-icon">📁</div>
        <p>Click or drag files here to upload</p>
        <p class="upload-hint">{{ selectedType === 'image' ? 'Images: JPG, PNG, GIF' : 'Videos: MP4, WebM, MOV' }}</p>
      </div>
      <div v-else class="uploaded-files">
        <div
          v-for="(file, idx) in files"
          :key="idx"
          class="file-item"
        >
          <div v-if="selectedType === 'image'" class="file-preview">
            <img :src="previewUrl(file)" :alt="file.name" />
          </div>
          <div v-else class="file-preview">
            <video :src="previewUrl(file)" preload="metadata" />
            <div class="video-duration">{{ formatFileSize(file.size) }}</div>
          </div>
          <button class="remove-file" @click.stop="removeFile(idx)">×</button>
        </div>
        <div v-if="files.length < maxFiles" class="add-more" @click.stop="triggerFileInput">
          <span>+</span>
        </div>
      </div>
    </div>

    <div v-if="uploading" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
      </div>
      <p>Uploading... {{ uploadProgress }}%</p>
    </div>

    <div v-if="uploadedFileIds.length > 0" class="uploaded-count">
      <p>✓ {{ uploadedFileIds.length }} file(s) uploaded successfully</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { mediaApi } from '../../api/media';

const emit = defineEmits(['uploaded', 'removed']);

const mediaTypes = [
  { value: 'image', label: 'Images', icon: '📷' },
  { value: 'video', label: 'Videos', icon: '🎬' }
];

const selectedType = ref('image');
const files = ref([]);
const uploadedFileIds = ref([]);
const uploading = ref(false);
const uploadProgress = ref(0);
const fileInput = ref(null);
const maxFiles = 9;

const selectType = (type) => {
  selectedType.value = type;
  files.value = [];
  uploadedFileIds.value = [];
};

const triggerFileInput = () => {
  fileInput.value.click();
};

const handleFileSelect = (event) => {
  const newFiles = Array.from(event.target.files);
  addFiles(newFiles);
  event.target.value = '';
};

const handleDrop = (event) => {
  const newFiles = Array.from(event.dataTransfer.files);
  addFiles(newFiles);
};

const addFiles = (newFiles) => {
  if (files.value.length + newFiles.length > maxFiles) {
    alert(`Maximum ${maxFiles} files allowed`);
    return;
  }

  // Validate file types
  const validFiles = newFiles.filter(file => {
    if (selectedType.value === 'image') {
      return file.type.startsWith('image/');
    } else {
      return file.type.startsWith('video/');
    }
  });

  if (validFiles.length !== newFiles.length) {
    alert('Some files were not added due to invalid type');
  }

  files.value = [...files.value, ...validFiles];
};

const removeFile = (index) => {
  const removedFile = files.value[index];
  files.value.splice(index, 1);

  if (uploadedFileIds.value[index]) {
    emit('removed', uploadedFileIds.value[index]);
    uploadedFileIds.value.splice(index, 1);
  }
};

const previewUrl = (file) => {
  return URL.createObjectURL(file);
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

const uploadAll = async () => {
  if (files.value.length === 0) {
    return [];
  }

  uploading.value = true;
  uploadProgress.value = 0;

  try {
    const uploadedIds = [];

    for (let i = 0; i < files.value.length; i++) {
      const file = files.value[i];
      const response = await mediaApi.upload(file, selectedType.value);

      if (response.success && response.data) {
        uploadedIds.push(response.data.file_id);
        uploadedFileIds.value.push(response.data.file_id);
        emit('uploaded', response.data.file_id);
      }

      uploadProgress.value = Math.round(((i + 1) / files.value.length) * 100);
    }

    uploading.value = false;
    return uploadedIds;
  } catch (err) {
    console.error('Upload failed:', err);
    uploading.value = false;
    throw err;
  }
};

defineExpose({
  uploadAll,
  uploadedFileIds
});
</script>

<style scoped>
.media-uploader {
  margin-bottom: 20px;
}

.media-type-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.type-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.type-button:hover {
  border-color: #409eff;
}

.type-button.active {
  border-color: #409eff;
  background: #e3f2fd;
}

.type-icon {
  font-size: 20px;
}

.type-label {
  font-weight: 500;
  color: #333;
}

.upload-area {
  border: 2px dashed #e0e0e0;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area:hover {
  border-color: #409eff;
  background: #f8f9fa;
}

.upload-placeholder {
  color: #999;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.upload-hint {
  font-size: 12px;
  color: #bbb;
  margin-top: 8px;
}

.uploaded-files {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
  width: 100%;
}

.file-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.file-preview {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-preview img,
.file-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-duration {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
}

.remove-file {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.7);
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

.remove-file:hover {
  background: rgba(244, 67, 54, 0.9);
}

.add-more {
  aspect-ratio: 1;
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #999;
  cursor: pointer;
}

.add-more:hover {
  border-color: #409eff;
  color: #409eff;
}

.upload-progress {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #66b1ff);
  transition: width 0.3s;
}

.upload-progress p {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin: 0;
}

.uploaded-count {
  margin-top: 12px;
  padding: 12px;
  background: #e8f5e9;
  color: #4caf50;
  border-radius: 8px;
  text-align: center;
}

.uploaded-count p {
  margin: 0;
  font-size: 14px;
}
</style>
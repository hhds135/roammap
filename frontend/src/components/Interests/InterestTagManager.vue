<template>
  <div class="interest-tag-manager">
    <h3>Interest Tags</h3>
    <p class="description">Add tags you're interested in, and the system will recommend related content.</p>

    <div class="add-tag-section">
      <input
        v-model="newTag"
        type="text"
        placeholder="Add new tag"
        @keyup.enter="handleAddTag"
      />
      <button @click="handleAddTag" :disabled="!newTag.trim()">Add</button>
    </div>

    <div class="tags-list">
      <span
        v-for="(tag, idx) in tags"
        :key="idx"
        class="tag-chip"
      >
        #{{ tag }}
        <button @click="handleRemoveTag(tag)" class="remove">×</button>
      </span>
    </div>

    <div v-if="tags.length === 0" class="empty-tags">
      <p>No tags added yet</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useAuth } from '../../composables/useAuth';
import { usersApi } from '../../api/users';

const { user } = useAuth();

const tags = ref([]);
const newTag = ref('');

const loadTags = async () => {
  if (!user.value) return;

  try {
    const response = await usersApi.getInterests(user.value.id);
    if (response.success && response.data) {
      tags.value = response.data.interest_tags || [];
    }
  } catch (err) {
    console.error('Failed to load interest tags', err);
  }
};

const handleAddTag = async () => {
  const trimmedTag = newTag.value.trim();

  if (!trimmedTag) return;
  if (tags.value.includes(trimmedTag)) {
    alert('Tag already exists');
    return;
  }

  const updatedTags = [...tags.value, trimmedTag];
  tags.value = updatedTags;
  newTag.value = '';

  await saveTags(updatedTags);
};

const handleRemoveTag = async (tagToRemove) => {
  const updatedTags = tags.value.filter(tag => tag !== tagToRemove);
  tags.value = updatedTags;

  await saveTags(updatedTags);
};

const saveTags = async (updatedTags) => {
  if (!user.value) return;

  try {
    await usersApi.updateInterests(user.value.id, updatedTags);
  } catch (err) {
    console.error('Failed to save interest tags', err);
  }
};

onMounted(() => {
  loadTags();
});
</script>

<style scoped>
.interest-tag-manager {
  padding: 20px;
}

.interest-tag-manager h3 {
  margin-bottom: 10px;
  color: #333;
}

.description {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.add-tag-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.add-tag-section input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.add-tag-section input:focus {
  outline: none;
  border-color: #409eff;
}

.add-tag-section button {
  padding: 10px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.add-tag-section button:hover {
  background: #66b1ff;
}

.add-tag-section button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background: #f5f5f5;
  border-radius: 20px;
  font-size: 14px;
}

.remove {
  margin-left: 8px;
  padding: 0 4px;
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.remove:hover {
  color: #f56c6c;
}

.empty-tags {
  padding: 40px;
  text-align: center;
  color: #999;
}
</style>
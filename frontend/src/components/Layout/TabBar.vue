<template>
  <div class="tab-bar">
    <router-link
      v-for="tab in tabs"
      :key="tab.path"
      :to="tab.path"
      :class="['tab-item', { active: isActive(tab.path) }]"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span class="tab-label">{{ tab.label }}</span>
    </router-link>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const tabs = [
  { path: '/feed', label: 'Feed', icon: '📱' },
  { path: '/map', label: 'Map', icon: '🗺️' },
  { path: '/create', label: 'Create', icon: '➕' },
  { path: '/interests', label: 'Tags', icon: '🏷️' },
  { path: '/profile', label: 'Profile', icon: '👤' }
];

const isActive = (path) => {
  return route.path.startsWith(path);
};
</script>

<style scoped>
.tab-bar {
  background: white;
  display: flex;
  justify-content: space-around;
  padding: 10px 0;
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.1);
  z-index: 100;
  flex-shrink: 0;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: #999;
  font-size: 12px;
  transition: all 0.3s;
}

.tab-icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.tab-label {
  font-size: 12px;
}

.tab-item.active {
  color: #409eff;
}
</style>